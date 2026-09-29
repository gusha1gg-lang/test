import React, { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import ServiceGraph from './pages/ServiceGraph';
import Calendar from './pages/Calendar';
import WorksList from './pages/WorksList';
import NewWork from './pages/NewWork';
import Settings from './pages/Settings';
import SlaReport from './pages/SlaReport';
import BackendDocs from './pages/BackendDocs';
import { PageType } from './types';

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard');
  const [selectedService, setSelectedService] = useState<string>('');

  const handleNavigate = useCallback((page: PageType) => {
    setCurrentPage(page);
  }, []);

  const handleServiceSelect = useCallback((serviceName: string) => {
    setSelectedService(serviceName);
  }, []);

  const handleNavigateToNewWork = useCallback(() => {
    setCurrentPage('new-work');
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'graph':
        return (
          <ServiceGraph
            onServiceSelect={handleServiceSelect}
            onNavigateToNewWork={handleNavigateToNewWork}
          />
        );
      case 'new-work':
        return <NewWork preselectedService={selectedService} />;
      case 'works-list':
        return <WorksList />;
      case 'calendar':
        return <Calendar onNavigateToNewWork={handleNavigateToNewWork} />;
      case 'sla-report':
        return <SlaReport />;
      case 'settings':
        return <Settings />;
      case 'backend-docs':
        return <BackendDocs />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-[#f5f5f5] overflow-hidden">
      {/* Боковая панель */}
      <Sidebar currentPage={currentPage} onNavigate={handleNavigate} />

      {/* Основная область */}
      <div className="flex-1 ml-[250px] flex flex-col h-screen overflow-hidden">
        {/* Шапка */}
        <Header currentPage={currentPage} />

        {/* Контент страницы */}
        <main className="flex-1 overflow-y-auto">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

export default App;
