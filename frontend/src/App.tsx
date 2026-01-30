import { Routes, Route, Link } from 'react-router-dom';
import PeopleGrid from './components/People/PeopleGrid';
import PersonDetail from './components/People/PersonDetail';
import ImageUpload from './components/Upload/ImageUpload';
import ImageGrid from './components/Images/ImageGrid';
import ImageDetail from './components/Images/ImageDetail';
import Navbar from './components/Layout/Navbar';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<PeopleGrid />} />
          <Route path="/people" element={<PeopleGrid />} />
          <Route path="/people/:groupId" element={<PersonDetail />} />
          <Route path="/upload" element={<ImageUpload />} />
          <Route path="/images" element={<ImageGrid />} />
          <Route path="/images/:imageId" element={<ImageDetail />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
