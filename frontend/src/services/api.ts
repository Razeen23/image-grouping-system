/** API client for backend communication */
import axios from 'axios';
import type { Image, Face, PersonGroup, UploadResponse, ProcessingStatus } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Images API
export const imagesApi = {
  list: async (skip = 0, limit = 100): Promise<Image[]> => {
    console.log('📋 Fetching images list:', { skip, limit });
    const response = await api.get('/images', { params: { skip, limit } });
    console.log('✅ Images list loaded:', { count: response.data.length });
    return response.data;
  },
  
  get: async (id: string): Promise<Image> => {
    console.log('📸 Fetching image:', id);
    const response = await api.get(`/images/${id}`);
    console.log('✅ Image data:', response.data);
    return response.data;
  },
  
  getFaces: async (id: string): Promise<Face[]> => {
    console.log('👤 Fetching faces for image:', id);
    const response = await api.get(`/images/${id}/faces`);
    console.log('✅ Faces data:', { count: response.data.length, faces: response.data });
    return response.data;
  },
  
  getImageUrl: (id: string): string => {
    return `/api/images/${id}/file`;
  },
  
  retryProcessing: async (id: string): Promise<void> => {
    console.log('🔄 Retrying processing for image:', id);
    const response = await api.post(`/images/${id}/retry`);
    console.log('✅ Retry response:', response.data);
    return response.data;
  },
  
  getDetectionDebug: async (id: string): Promise<any> => {
    console.log('🔍 Getting detection debug info for image:', id);
    const response = await api.get(`/images/${id}/detection-debug`);
    console.log('✅ Detection debug info:', response.data);
    return response.data;
  },
};

// Faces API
export const facesApi = {
  list: async (skip = 0, limit = 100): Promise<Face[]> => {
    const response = await api.get('/faces', { params: { skip, limit } });
    return response.data;
  },
  
  get: async (id: string): Promise<Face> => {
    const response = await api.get(`/faces/${id}`);
    return response.data;
  },
};

// Groups API
export const groupsApi = {
  list: async (skip = 0, limit = 100): Promise<PersonGroup[]> => {
    const response = await api.get('/groups', { params: { skip, limit } });
    return response.data;
  },
  
  get: async (id: string): Promise<PersonGroup> => {
    const response = await api.get(`/groups/${id}`);
    return response.data;
  },
  
  getFaces: async (id: string): Promise<Face[]> => {
    const response = await api.get(`/groups/${id}/faces`);
    return response.data;
  },
  
  getImages: async (id: string): Promise<Image[]> => {
    const response = await api.get(`/groups/${id}/images`);
    return response.data;
  },
  
  merge: async (sourceId: string, targetId: string): Promise<void> => {
    await api.post(`/groups/${sourceId}/merge`, { target_group_id: targetId });
  },
  
  delete: async (id: string): Promise<void> => {
    await api.delete(`/groups/${id}`);
  },
};

// Upload API
export const uploadApi = {
  upload: async (files: File[]): Promise<UploadResponse[]> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Processing API
export const processingApi = {
  trigger: async (imageId: string): Promise<void> => {
    await api.post(`/process/${imageId}`);
  },
  
  getStatus: async (): Promise<ProcessingStatus> => {
    const response = await api.get('/processing/status');
    return response.data;
  },
};
