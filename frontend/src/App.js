import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import DealDetail from './pages/DealDetail';
import Templates from './pages/Templates';
import UserSettings from './pages/UserSettings';
import DocumentQuestions from './components/DocumentQuestions';
import DealQuestions from './components/DealQuestions';
import ProtectedRoute from './components/ProtectedRoute';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <Router>
          <div className="App">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/projects" element={
                <ProtectedRoute>
                  <Layout>
                    <Projects />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/projects/:projectId" element={
                <ProtectedRoute>
                  <Layout>
                    <ProjectDetail />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/projects/:projectId/:tab" element={
                <ProtectedRoute>
                  <Layout>
                    <ProjectDetail />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/deals/:dealId" element={
                <ProtectedRoute>
                  <Layout>
                    <DealDetail />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/deals/:dealId/questions" element={
                <ProtectedRoute>
                  <Layout>
                    <DealQuestions />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/deals/:dealId/documents/:documentId/questions" element={
                <ProtectedRoute>
                  <Layout>
                    <DocumentQuestions />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/templates" element={
                <ProtectedRoute>
                  <Layout>
                    <Templates />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/settings" element={
                <ProtectedRoute>
                  <Layout>
                    <UserSettings />
                  </Layout>
                </ProtectedRoute>
              } />
            </Routes>
          </div>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;