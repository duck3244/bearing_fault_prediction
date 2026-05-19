#!/usr/bin/env python
"""Train the bearing fault classifier on the MFPT dataset and persist it.

Usage:
    python scripts/train_mfpt.py <train_dir> [--out PATH] [--test-dir DIR]
                                 [--preset NAME] [--window N] [--hop N]

Examples:
    python scripts/train_mfpt.py /path/to/MFPT_Dataset/train \
        --test-dir /path/to/MFPT_Dataset/test \
        --out models/classifier.pkl
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

# Make project root importable when invoked as a script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.bearing_calculations import calculate_bearing_frequencies  # noqa: E402
from app.core.bearing_presets import BEARING_PRESETS, preset_to_bearing_params  # noqa: E402
from app.core.fault_classifier import BearingFaultClassifier  # noqa: E402
from app.core.feature_extraction import (  # noqa: E402
    extract_frequency_domain_features,
    extract_time_domain_features,
)
from app.core.mat_loader import label_from_filename, load_mat_signal  # noqa: E402
from app.core.spectral_analysis import perform_fft  # noqa: E402


def evaluate(clf, test_dir, bearing_params, window, hop, default_rpm, default_sr):
    files = sorted(f for f in os.listdir(test_dir) if f.lower().endswith('.mat'))
    correct = total = 0
    win_correct = win_total = 0
    print(f'\n{"file":40s}  {"expected":12s}  {"voted":12s}  win_acc')
    print('-' * 90)
    for fname in files:
        label = label_from_filename(fname)
        if label is None:
            continue
        mat = load_mat_signal(os.path.join(test_dir, fname))
        sig = mat['signal']
        sr = mat['sampling_rate'] or default_sr
        rpm = mat['rpm'] or default_rpm
        ff = calculate_bearing_frequencies(rpm, bearing_params)
        preds = []
        for start in range(0, len(sig) - window + 1, max(1, hop)):
            seg = sig[start:start + window]
            tf = extract_time_domain_features(seg)
            freq, mag = perform_fft(seg, sr)
            ffeat = extract_frequency_domain_features(freq, mag, ff)
            p, _, _ = clf.predict(tf, ffeat)
            preds.append(p)
        if not preds:
            continue
        voted = max(set(preds), key=preds.count)
        ok = (voted == label)
        correct += int(ok); total += 1
        win_correct += preds.count(label); win_total += len(preds)
        print(f'{fname:40s}  {label:12s}  {voted:12s}  {preds.count(label)}/{len(preds)}  {"OK" if ok else "FAIL"}')
    if total:
        print(f'\nFile-level: {correct}/{total} = {correct/total:.1%}')
        print(f'Window-level: {win_correct}/{win_total} = {win_correct/win_total:.1%}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('train_dir', help='Directory of MFPT-style .mat training files')
    ap.add_argument('--out', default='models/classifier.pkl', help='Where to save the trained model')
    ap.add_argument('--test-dir', default=None, help='Optional held-out test directory')
    ap.add_argument('--preset', default='MFPT-NICE', choices=list(BEARING_PRESETS))
    ap.add_argument('--window', type=int, default=12000)
    ap.add_argument('--hop', type=int, default=6000)
    ap.add_argument('--augment', type=int, default=4,
                    help='Amplitude-augmentation copies per window (1 disables aug). '
                         'Default 4 fixes the MFPT amplitude-shortcut issue.')
    ap.add_argument('--augment-min', type=float, default=0.3)
    ap.add_argument('--augment-max', type=float, default=3.0)
    args = ap.parse_args()

    bearing_params = preset_to_bearing_params(args.preset)
    preset = BEARING_PRESETS[args.preset]

    print(f'Preset: {args.preset} ({preset["description"]})')
    print(f'  bearing_params={bearing_params}')
    print(f'  default_rpm={preset["default_rpm"]} default_sr={preset["default_sampling_rate"]}')
    print(f'\nTraining on: {args.train_dir}')

    clf = BearingFaultClassifier()
    meta = clf.train_from_dataset(
        args.train_dir,
        bearing_params=bearing_params,
        window=args.window,
        hop=args.hop,
        default_rpm=preset['default_rpm'],
        default_sampling_rate=preset['default_sampling_rate'],
        amplitude_augment=args.augment,
        augment_scale_range=(args.augment_min, args.augment_max),
    )
    print(f'  files: {meta["n_files"]}, windows: {meta["n_windows"]} '
          f'(augment={meta["amplitude_augment"]})')
    print(f'  class counts: {meta["class_counts"]}')
    if meta['skipped_files']:
        print(f'  skipped (no label match): {meta["skipped_files"]}')

    clf.save(args.out)
    print(f'\nSaved to {os.path.abspath(args.out)}')

    if args.test_dir:
        evaluate(clf, args.test_dir, bearing_params, args.window, args.hop,
                 preset['default_rpm'], preset['default_sampling_rate'])


if __name__ == '__main__':
    main()
