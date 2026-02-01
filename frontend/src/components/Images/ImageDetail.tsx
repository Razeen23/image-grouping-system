import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { imagesApi } from '../../services/api';

export default function ImageDetail() {
  const { imageId } = useParams<{ imageId: string }>();
  const queryClient = useQueryClient();

  const { data: image, isLoading: imageLoading } = useQuery({
    queryKey: ['image', imageId],
    queryFn: () => {
      console.log('📸 Fetching image details for:', imageId);
      return imagesApi.get(imageId!);
    },
    enabled: !!imageId,
    refetchInterval: (query) => {
      // Poll for status updates if image is processing
      const data = query.state.data as any;
      if (data?.processing_status === 'processing' || data?.processing_status === 'pending') {
        return 2000; // Poll every 2 seconds while processing
      }
      return false; // Don't poll if completed or failed
    },
    onSuccess: (data) => {
      console.log('✅ Image loaded:', {
        id: data.id,
        filename: data.filename,
        status: data.processing_status,
        processed_at: data.processed_at,
      });
      if (data.processing_status === 'processing') {
        console.log('⏳ Image is currently being processed...');
      } else if (data.processing_status === 'completed') {
        console.log('✅ Image processing completed');
      } else if (data.processing_status === 'failed') {
        console.error('❌ Image processing failed');
      }
    },
  });

  const { data: faces, isLoading: facesLoading } = useQuery({
    queryKey: ['image-faces', imageId],
    queryFn: () => {
      console.log('👤 Fetching faces for image:', imageId);
      return imagesApi.getFaces(imageId!);
    },
    enabled: !!imageId,
    onSuccess: (data) => {
      console.log('✅ Faces loaded:', {
        count: data.length,
        faces: data.map(f => ({
          id: f.id,
          confidence: f.confidence,
          person_group_id: f.person_group_id,
        })),
      });
      if (data.length === 0) {
        console.warn('⚠️ No faces detected in this image');
      }
    },
  });

  const retryMutation = useMutation({
    mutationFn: () => {
      console.log('🔄 Starting face detection retry for image:', imageId);
      return imagesApi.retryProcessing(imageId!);
    },
    onSuccess: (data) => {
      console.log('✅ Retry initiated:', data);
      // Refetch image data to get updated status
      queryClient.invalidateQueries({ queryKey: ['image', imageId] });
      queryClient.invalidateQueries({ queryKey: ['images'] });
      queryClient.invalidateQueries({ queryKey: ['image-faces', imageId] });
      queryClient.invalidateQueries({ queryKey: ['groups'] });
      console.log('🔄 Queries invalidated, will refetch data...');
    },
    onError: (error) => {
      console.error('❌ Retry failed:', error);
    },
  });

  const debugMutation = useMutation({
    mutationFn: () => {
      console.log('🔍 Running detection debug test for image:', imageId);
      return imagesApi.getDetectionDebug(imageId!);
    },
    onSuccess: (data) => {
      console.log('🔍 Detection Debug Results:', data);
      if (data.detection_results) {
        console.log(`   Faces detected: ${data.detection_results.faces_detected}`);
        if (data.detection_results.detections && data.detection_results.detections.length > 0) {
          data.detection_results.detections.forEach((det: any, idx: number) => {
            console.log(`   Face ${idx + 1}: confidence=${det.confidence.toFixed(4)}, bbox=${det.bbox}, size=${det.bbox_size}`);
          });
        } else {
          console.warn('   ⚠️ No faces detected in debug test');
        }
      }
      if (data.error) {
        console.error('   ❌ Debug test error:', data.error);
      }
    },
    onError: (error) => {
      console.error('❌ Debug test failed:', error);
    },
  });

  if (imageLoading || facesLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!image) {
    return <div className="text-center text-red-600">Image not found</div>;
  }

  return (
    <div>
      <button
        onClick={() => window.history.back()}
        className="mb-4 text-blue-600 hover:text-blue-700"
      >
        ← Back
      </button>

      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold mb-4">{image.filename}</h1>

        <div className="mb-6 relative">
          <img
            src={imagesApi.getImageUrl(image.id)}
            alt={image.filename}
            className="max-w-full h-auto rounded-lg"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              const parent = target.parentElement;
              if (parent && !parent.querySelector('.error-fallback')) {
                const fallback = document.createElement('div');
                fallback.className = 'error-fallback w-full h-64 flex items-center justify-center text-gray-400 bg-gray-100 rounded-lg';
                fallback.textContent = 'Failed to load image';
                parent.appendChild(fallback);
              }
            }}
          />
          {/* TODO: Overlay bounding boxes for detected faces */}
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold">Status:</span>
            <span className={`px-2 py-1 rounded text-sm ${
              image.processing_status === 'completed' ? 'bg-green-100 text-green-800' :
              image.processing_status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
              image.processing_status === 'failed' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {image.processing_status}
            </span>
            {(image.processing_status === 'failed' || image.processing_status === 'pending') && (
              <button
                onClick={() => retryMutation.mutate()}
                disabled={retryMutation.isPending}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {retryMutation.isPending ? 'Retrying...' : 'Retry Processing'}
              </button>
            )}
            {image.processing_status === 'completed' && (
              <>
                <button
                  onClick={() => retryMutation.mutate()}
                  disabled={retryMutation.isPending}
                  className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Redo face detection with improved settings"
                >
                  {retryMutation.isPending ? 'Redetecting...' : 'Redo Face Detection'}
                </button>
                <button
                  onClick={() => debugMutation.mutate()}
                  disabled={debugMutation.isPending}
                  className="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Test face detection and see detailed results in console"
                >
                  {debugMutation.isPending ? 'Testing...' : '🔍 Test Detection'}
                </button>
              </>
            )}
          </div>

          {image.processing_status === 'completed' && (
            <div>
              {faces && faces.length > 0 ? (
                <div>
                  <span className="font-semibold">Faces Detected:</span> {faces.length}
                  <div className="mt-2 space-y-1">
                    {faces.map((face) => (
                      <div key={face.id} className="text-sm text-gray-600">
                        Face {face.id.slice(0, 8)} - Confidence: {face.confidence?.toFixed(2) || 'N/A'}
                        {face.person_group_id && (
                          <span className="ml-2 text-blue-600">
                            (Person Group: {face.person_group_id.slice(0, 8)})
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-yellow-800 font-semibold">No faces detected in this image</p>
                  <p className="text-yellow-700 text-sm mt-1">
                    This image was processed but no faces were found. This could mean:
                  </p>
                  <ul className="text-yellow-700 text-sm mt-2 list-disc list-inside space-y-1">
                    <li>The image doesn't contain any visible faces</li>
                    <li>Faces are too small or unclear</li>
                    <li>The face detection model couldn't identify faces in this image</li>
                  </ul>
                  <p className="text-yellow-700 text-sm mt-2">
                    <strong>Note:</strong> Person groups are only created when faces are detected. 
                    If no faces are detected in any images, you won't see any person groups on the People page.
                  </p>
                  <button
                    onClick={() => retryMutation.mutate()}
                    disabled={retryMutation.isPending}
                    className="mt-3 px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {retryMutation.isPending ? 'Redetecting Faces...' : '🔄 Redo Face Detection'}
                  </button>
                </div>
              )}
              {faces && faces.length > 0 && (
                <div className="mt-3">
                  <button
                    onClick={() => retryMutation.mutate()}
                    disabled={retryMutation.isPending}
                    className="px-4 py-2 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Reprocess this image to detect faces again (existing faces will be removed)"
                  >
                    {retryMutation.isPending ? 'Redetecting...' : '🔄 Redo Face Detection'}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
