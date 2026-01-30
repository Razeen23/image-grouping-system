import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { imagesApi } from '../../services/api';
import ImageCard from './ImageCard';

export default function ImageGrid() {
  const { data: images, isLoading, error } = useQuery({
    queryKey: ['images'],
    queryFn: () => imagesApi.list(0, 100),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600">
        Error loading images: {(error as Error).message}
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">All Images</h1>
        <Link
          to="/upload"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Upload Images
        </Link>
      </div>

      {!images || images.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600 mb-4">No images found.</p>
          <Link
            to="/upload"
            className="text-blue-600 hover:text-blue-700 underline"
          >
            Upload some images to get started
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {images.map((image) => (
            <ImageCard key={image.id} image={image} />
          ))}
        </div>
      )}
    </div>
  );
}
