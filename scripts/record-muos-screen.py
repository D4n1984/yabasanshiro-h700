#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# H700 / muOS utilities by D4n1984.
"""Read the muOS framebuffer over SSH and encode an MP4 on the host PC.

Requires host Python paramiko, host ffmpeg and device Python 3. No device files
are written. Capture excludes audio; use separate runs for performance timing.
"""
import argparse
import getpass
import json
from pathlib import Path
import shlex
import shutil
import struct
import subprocess
import sys
import zlib

import paramiko

DEVICE_CAPTURE = r'''
import fcntl,json,struct,sys,time,zlib
fps,seconds=float(sys.argv[1]),float(sys.argv[2])
out=sys.stdout.buffer
with open('/dev/fb0','rb',buffering=0) as fb:
    var=bytearray(160);fix=bytearray(80)
    fcntl.ioctl(fb,0x4600,var);fcntl.ioctl(fb,0x4602,fix)
    w,h,_,_,_,_,bpp,_=struct.unpack_from('8I',var)
    stride=struct.unpack_from('I',fix,48)[0]
    # Each fb_bitfield has offset, length and msb_right (three uint32 fields).
    channels=tuple(struct.unpack_from('I',var,n)[0] for n in (32,44,56))
    formats={(16,8,0):'bgra',(0,8,16):'rgba'}
    assert bpp==32 and channels in formats, 'Expected a 32-bit RGB framebuffer'
    out.write((json.dumps({'width':w,'height':h,'pixel_format':formats[channels],'fps_requested':fps,'audio':False})+'\n').encode());out.flush()
    start=time.monotonic();next_frame=start
    while time.monotonic()-start < seconds:
        time.sleep(max(0,next_frame-time.monotonic()))
        fcntl.ioctl(fb,0x4600,var)
        assert struct.unpack_from('2I',var)==(w,h), 'Display mode changed during recording'
        assert tuple(struct.unpack_from('I',var,n)[0] for n in (32,44,56))==channels, 'Display pixel format changed during recording'
        x,y=struct.unpack_from('2I',var,16)
        fb.seek(y*stride);raw=fb.read(h*stride)
        if stride!=w*4 or x:
            raw=b''.join(raw[r*stride+x*4:r*stride+x*4+w*4] for r in range(h))
        stamp=time.monotonic()-start
        payload=zlib.compress(raw,1)
        out.write(struct.pack('<dI',stamp,len(payload)));out.write(payload);out.flush()
        next_frame=max(next_frame+1/fps,time.monotonic())
'''


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    parser.add_argument('--user', default='root')
    parser.add_argument('--known-hosts', type=Path, default=Path.home()/'.ssh/known_hosts')
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--fps', type=float, default=15)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not (0 < args.seconds <= 600 and 0 < args.fps <= 60):
        parser.error('seconds must be in (0, 600], fps in (0, 60]')
    if not shutil.which('ffmpeg'):
        parser.error('Install ffmpeg on the host PC first')
    if args.output.exists():
        parser.error('Output already exists; choose a new filename')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    return args


def record_screen(client, args):
    """Capture using an authenticated SSH connection (also used by A/B runs)."""
    command = 'python3 -u -c ' + shlex.quote(DEVICE_CAPTURE) + ' ' + str(args.fps) + ' ' + str(args.seconds)
    _, stream, errors = client.exec_command(command)
    encoder = None
    stamps = []
    encoded = 0
    previous = None
    target_frames = max(1, round(args.seconds * args.fps))
    try:
        header = stream.readline()
        if not header:
            raise RuntimeError(errors.read().decode(errors='replace'))
        metadata = json.loads(header)
        size = metadata['width'] * metadata['height'] * 4
        encoder = subprocess.Popen([
            'ffmpeg', '-hide_banner', '-loglevel', 'warning', '-n',
            '-f', 'rawvideo', '-pixel_format', metadata['pixel_format'], '-video_size',
            f"{metadata['width']}x{metadata['height']}", '-framerate', str(args.fps),
            '-i', 'pipe:0', '-an', '-c:v', 'libx264', '-preset', 'veryfast',
            '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(args.output)
        ], stdin=subprocess.PIPE)
        print(f"Recording {metadata['width']}x{metadata['height']} at up to {args.fps:g} fps, without audio", flush=True)
        while True:
            packet = stream.read(12)
            if not packet:
                break
            if len(packet) != 12:
                raise RuntimeError('Truncated capture header')
            timestamp, count = struct.unpack('<dI', packet)
            if not 0 < count <= size * 2:
                raise RuntimeError('Invalid capture frame length')
            frame = zlib.decompress(stream.read(count))
            if len(frame) != size:
                raise RuntimeError('Incomplete framebuffer capture')
            # Resample by the device timestamps so a slow SSH capture cannot
            # accelerate the video. Repeat the previous image across gaps.
            target = min(target_frames, round(timestamp * args.fps))
            while encoded < target:
                encoder.stdin.write(previous if previous is not None else frame)
                encoded += 1
            previous = frame
            stamps.append(timestamp)
        status = stream.channel.recv_exit_status()
        if status:
            raise RuntimeError(errors.read().decode(errors='replace'))
    finally:
        stream.channel.close()
        if encoder:
            if previous is not None:
                while encoded < target_frames:
                    encoder.stdin.write(previous)
                    encoded += 1
            encoder.stdin.close()
            encoder.wait()
    if not stamps or encoder.returncode:
        raise RuntimeError('Recording or video encoding failed')
    metadata.update(frame_count=len(stamps), encoded_frame_count=encoded,
                    timestamps_seconds=stamps, timing='device timestamps; repeated frames across capture gaps',
                    duration_requested=args.seconds, video_duration_seconds=encoded/args.fps,
                    capture_elapsed_seconds=stamps[-1]-stamps[0],
                    fps_actual=(len(stamps)-1)/(stamps[-1]-stamps[0]) if len(stamps)>1 else 0)
    args.output.with_suffix('.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(f"Saved {args.output}: {len(stamps)} frames, capture {metadata['fps_actual']:.2f} fps")
    return metadata


def main():
    args = parse_args()
    client = paramiko.SSHClient()
    client.load_host_keys(str(args.known_hosts))
    try:
        client.connect(args.host, username=args.user, password=getpass.getpass('Device password: '),
                       look_for_keys=False, allow_agent=False, timeout=10)
        client.get_transport().set_keepalive(10)
        record_screen(client, args)
    finally:
        client.close()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, paramiko.SSHException, KeyboardInterrupt) as error:
        print(f'Recording failed: {error}', file=sys.stderr)
        sys.exit(1)
