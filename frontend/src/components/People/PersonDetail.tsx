import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { groupsApi } from '../../services/api';
import PersonPhotos from './PersonPhotos';

export default function PersonDetail() {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();

  const { data: group, isLoading: groupLoading } = useQuery({
    queryKey: ['group', groupId],
    queryFn: () => groupsApi.get(groupId!),
    enabled: !!groupId,
  });

  const { data: images, isLoading: imagesLoading } = useQuery({
    queryKey: ['group-images', groupId],
    queryFn: () => groupsApi.getImages(groupId!),
    enabled: !!groupId,
  });

  if (groupLoading || imagesLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!group) {
    return <div className="text-center text-red-600">Person group not found</div>;
  }

  const displayName = group.name || `Person ${group.id.slice(0, 8)}`;

  return (
    <div>
      <button
        onClick={() => navigate('/people')}
        className="mb-4 text-blue-600 hover:text-blue-700"
      >
        ← Back to People
      </button>
      <h1 className="text-3xl font-bold mb-6">{displayName}</h1>
      <PersonPhotos groupId={groupId!} images={images || []} />
    </div>
  );
}
