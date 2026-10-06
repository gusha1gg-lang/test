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
import Users from './pages/Users';
import Groups from './pages/Groups';
import Audit from './pages/Audit';
import { PageType } from './types';

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard');
  const [selectedService, setSelectedService] = useState<string>('');
  const [selectedServiceId, setSelectedServiceId] = useState<string>('');

  const handleNavigate = useCallback((page: PageType) => {
    setCurrentPage(page);
  }, []);

  const handleServiceSelect = useCallback((serviceName: string, serviceId?: string) => {
    setSelectedService(serviceName);
    setSelectedServiceId(serviceId || '');
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
        return <NewWork preselectedService={selectedService} preselectedServiceId={selectedServiceId} />;
      case 'works-list':
        return <WorksList />;
      case 'calendar':
        return <Calendar onNavigateToNewWork={handleNavigateToNewWork} />;
      case 'sla-report':
        return <SlaReport />;
      case 'users':
        return <Users />;
      case 'groups':
        return <Groups />;
      case 'audit':
        return <Audit />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-[#f5f5f5] overflow-hidden">
      <Sidebar currentPage={currentPage} onNavigate={handleNavigate} />
      <div className="flex-1 ml-[250px] flex flex-col h-screen overflow-hidden">
        <Header currentPage={currentPage} />
        <main className="flex-1 overflow-y-auto">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

export default App;
