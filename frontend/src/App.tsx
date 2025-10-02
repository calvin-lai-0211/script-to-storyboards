import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import ScriptsList from './pages/ScriptsList'
import Workspace from './pages/Workspace'
import Characters from './pages/Characters'
import Scenes from './pages/Scenes'
import Props from './pages/Props'
import CharacterViewer from './pages/CharacterViewer'
import SceneViewer from './pages/SceneViewer'

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<ScriptsList />} />
          <Route path="/episode/:key" element={<Workspace />} />
          <Route path="/characters" element={<Characters />} />
          <Route path="/scenes" element={<Scenes />} />
          <Route path="/props" element={<Props />} />
          <Route path="/character/:id" element={<CharacterViewer />} />
          <Route path="/scene/:id" element={<SceneViewer />} />
        </Routes>
      </MainLayout>
    </Router>
  )
}

export default App
