export default function UploadProgress() {
  return (
    <div className="mt-4 p-4 bg-blue-50 rounded-lg">
      <div className="flex items-center">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
        <span className="text-blue-700">Uploading and processing images...</span>
      </div>
    </div>
  );
}
