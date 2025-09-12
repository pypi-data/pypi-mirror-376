export type Color = readonly [number, number, number];

export const MISSING_CATEGORY: Color = [255, 0, 0]; // Red

export const CATEGORY_COLORS: Color[] = [
  [0, 255, 0], // Green
  [0, 0, 255], // Blue
  [255, 165, 0], // Orange
  [0, 255, 255], // Cyan
  [255, 255, 0], // Yellow
  [255, 0, 255], // Magenta
  [255, 69, 0], // Orange Red
  [255, 20, 147], // Deep Pink
  [255, 215, 0], // Gold
];

export const MODEL_COLORS: Color[] = [
  [255, 215, 0], // Gold
  [255, 20, 147], // Deep Pink
  [0, 255, 255], // Cyan
  [255, 0, 0], // Red
  [0, 255, 0], // Green
];

export type Box = [number, number, number, number];

export type Classification = {
  category_id: number;
  id?: number;
  label?: string; // fallback if category_id has no match
  score?: number;
  model_id?: number;
};

export type BoxAnnotation = Classification & {
  bbox: Box;
};

export type Annotation = Classification | BoxAnnotation;

export type AnnotationAugmentations = {
  color: Color;
  name: string;
  modelName?: string;
};

export type ClassificationAugmented = Classification & AnnotationAugmentations;

export type BoxAnnotationAugmented = BoxAnnotation & AnnotationAugmentations;
