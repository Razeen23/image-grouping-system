import { Link } from 'react-router-dom';
import type { Image } from '../../types';
import { imagesApi } from '../../services/api';

interface PersonPhotosProps {
  groupId: string;
  images: Image[];
}

export default function PersonPhotos({ images }: PersonPhotosProps) {
  if (images.length === 0) {
    return (
      <div className="text-center py-12 text-gray-600">
        No photos found for this person.
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">
        {images.length} {images.length === 1 ? 'Photo' : 'Photos'}
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {images.map((image) => (
          <Link
            key={image.id}
            to={`/images/${image.id}`}
            className="block aspect-square bg-gray-100 rounded-lg overflow-hidden hover:opacity-90 transition-opacity"
          >
            <img
              src={imagesApi.getImageUrl(image.id)}
              alt={image.filename}
              className="w-full h-full object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const parent = target.parentElement;
                if (parent && !parent.querySelector('.error-fallback')) {
                  const fallback = document.createElement('div');
                  fallback.className = 'error-fallback w-full h-full flex items-center justify-center text-gray-400';
                  fallback.textContent = 'No image';
                  parent.appendChild(fallback);
                }
              }}
            />
          </Link>
        ))}
      </div>
    </div>
  );
}
