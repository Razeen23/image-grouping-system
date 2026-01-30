import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { groupsApi, imagesApi } from '../../services/api';
import type { PersonGroup } from '../../types';

interface PersonCardProps {
  group: PersonGroup;
}

export default function PersonCard({ group }: PersonCardProps) {
  const { data: images } = useQuery({
    queryKey: ['group-images', group.id],
    queryFn: () => groupsApi.getImages(group.id),
    enabled: !!group.id,
  });

  const imageCount = images?.length || 0;
  const displayName = group.name || `Person ${group.id.slice(0, 8)}`;

  return (
    <Link
      to={`/people/${group.id}`}
      className="block bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200 overflow-hidden"
    >
      <div className="aspect-square bg-gray-100 flex items-center justify-center">
        {images && images.length > 0 ? (
          <img
            src={imagesApi.getImageUrl(images[0].id)}
            alt={displayName}
            className="w-full h-full object-cover"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              const parent = target.parentElement;
              if (parent && !parent.querySelector('.error-fallback')) {
                const fallback = document.createElement('div');
                fallback.className = 'error-fallback text-gray-400 text-4xl';
                fallback.textContent = '👤';
                parent.appendChild(fallback);
              }
            }}
          />
        ) : (
          <div className="text-gray-400 text-4xl">👤</div>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 truncate">{displayName}</h3>
        <p className="text-sm text-gray-500 mt-1">
          {imageCount} {imageCount === 1 ? 'photo' : 'photos'}
        </p>
      </div>
    </Link>
  );
}
