import { Link } from 'react-router-dom';
import type { Image } from '../../types';
import { imagesApi } from '../../services/api';

interface ImageCardProps {
  image: Image;
}

export default function ImageCard({ image }: ImageCardProps) {
  return (
    <Link
      to={`/images/${image.id}`}
      className="block aspect-square bg-gray-100 rounded-lg overflow-hidden hover:opacity-90 transition-opacity relative"
    >
      <img
        src={imagesApi.getImageUrl(image.id)}
        alt={image.filename}
        className="w-full h-full object-cover"
        onError={(e) => {
          // Fallback if image fails to load
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
      {image.processing_status !== 'completed' && (
        <div className="absolute top-2 right-2 bg-yellow-500 text-white text-xs px-2 py-1 rounded">
          {image.processing_status}
        </div>
      )}
    </Link>
  );
}
