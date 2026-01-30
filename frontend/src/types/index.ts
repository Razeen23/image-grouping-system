/** TypeScript interfaces for API responses */

export interface Image {
  id: string;
  filename: string;
  storage_key: string;
  storage_url: string | null;
  mime_type: string | null;
  file_size: number | null;
  width: number | null;
  height: number | null;
  uploaded_at: string;
  processed_at: string | null;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
}

export interface Face {
  id: string;
  image_id: string;
  bounding_box: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  confidence: number | null;
  detected_at: string;
  person_group_id: string | null;
}

export interface PersonGroup {
  id: string;
  name: string | null;
  representative_face_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface UploadResponse {
  image_id: string;
  filename: string;
  message: string;
}

export interface ProcessingStatus {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  total: number;
}
