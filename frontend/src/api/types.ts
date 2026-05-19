/**
 * Friendly aliases over the auto-generated OpenAPI schema.
 * Run `pnpm gen:api` whenever the backend Pydantic schemas change.
 */
import type { components } from './schema';

export type AnalyzeResponse = components['schemas']['AnalyzeResponse'];
export type Prediction = components['schemas']['Prediction'];
export type FaultFrequencies = components['schemas']['FaultFrequencies'];
export type FaultDetectionHit = components['schemas']['FaultDetectionHit'];
export type TimeFeatures = components['schemas']['TimeFeatures'];
export type ModelInfo = components['schemas']['ModelInfo'];
export type BearingPresetsResponse = components['schemas']['BearingPresetsResponse'];
export type BearingPresetApplyResponse = components['schemas']['BearingPresetApplyResponse'];
export type SampleDataResponse = components['schemas']['SampleDataResponse'];
export type SignalFeatures = components['schemas']['SignalFeatures'];
export type GenerateSampleRequest = components['schemas']['GenerateSampleRequest'];
export type RetrainRequest = components['schemas']['RetrainRequest'];
export type RetrainResponse = components['schemas']['RetrainResponse'];

export const FAULT_TYPES = [
  'normal',
  'outer_fault',
  'inner_fault',
  'ball_fault',
  'cage_fault',
] as const;
export type FaultType = (typeof FAULT_TYPES)[number];

export type FaultName = 'BPFO' | 'BPFI' | 'BSF' | 'FTF';

export const FAULT_NAMES: FaultName[] = ['BPFO', 'BPFI', 'BSF', 'FTF'];
