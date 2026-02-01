import { useQuery } from '@tanstack/react-query';
import { groupsApi } from '../../services/api';
import PersonCard from './PersonCard';
import { Link } from 'react-router-dom';

export default function PeopleGrid() {
  const { data: groups, isLoading, error } = useQuery({
    queryKey: ['groups'],
    queryFn: () => {
      console.log('👥 Fetching person groups...');
      return groupsApi.list(0, 100);
    },
    onSuccess: (data) => {
      console.log('✅ Person groups loaded:', {
        count: data.length,
        groups: data.map(g => ({ id: g.id, name: g.name })),
      });
      if (data.length === 0) {
        console.warn('⚠️ No person groups found. This usually means no faces were detected in any images.');
      }
    },
    onError: (err) => {
      console.error('❌ Error loading person groups:', err);
    },
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
        Error loading person groups: {(error as Error).message}
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">People</h1>
        <Link
          to="/upload"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Upload Images
        </Link>
      </div>

      {!groups || groups.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600 mb-4">No people groups found.</p>
          <Link
            to="/upload"
            className="text-blue-600 hover:text-blue-700 underline"
          >
            Upload some images to get started
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {groups.map((group) => (
            <PersonCard key={group.id} group={group} />
          ))}
        </div>
      )}
    </div>
  );
}
