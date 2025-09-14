import { 
  Bell, 
  ChevronLeft, 
  RotateCcw, 
  Search, 
  Settings, 
  User, 
  TrendingUp,
  AlertTriangle,
  Clock,
  CheckCircle,
  Activity,
  Award,
  Ticket,
  Loader2
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Badge } from "./components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { useMetrics } from "./hooks/useMetrics";
import { useRanking } from "./hooks/useRanking";
import { useTickets } from "./hooks/useTickets";
import { formatNumber, formatDate } from "./utils/formatters";
import { useEffect, useState } from "react";

export default function App() {
  const { data: metrics, loading: metricsLoading, refetch: refetchMetrics } = useMetrics();
  const { data: ranking, loading: rankingLoading } = useRanking();
  const { data: tickets, loading: ticketsLoading } = useTickets();
  const [currentTime, setCurrentTime] = useState(new Date());

  // Atualizar horário a cada segundo
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Handler para refresh manual
  const handleRefresh = () => {
    refetchMetrics();
  };

  // Loading state
  if (metricsLoading && !metrics) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#5A9BD4] animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Carregando dashboard...</p>
        </div>
      </div>
    );
  }

  // Calcular totais gerais se não vieram da API
  const totalGeral = metrics?.niveis?.geral || {
    novos: (metrics?.niveis?.n1?.novos || 0) + (metrics?.niveis?.n2?.novos || 0) + 
           (metrics?.niveis?.n3?.novos || 0) + (metrics?.niveis?.n4?.novos || 0),
    progresso: (metrics?.niveis?.n1?.progresso || 0) + (metrics?.niveis?.n2?.progresso || 0) + 
               (metrics?.niveis?.n3?.progresso || 0) + (metrics?.niveis?.n4?.progresso || 0),
    pendentes: (metrics?.niveis?.n1?.pendentes || 0) + (metrics?.niveis?.n2?.pendentes || 0) + 
               (metrics?.niveis?.n3?.pendentes || 0) + (metrics?.niveis?.n4?.pendentes || 0),
    resolvidos: (metrics?.niveis?.n1?.resolvidos || 0) + (metrics?.niveis?.n2?.resolvidos || 0) + 
                (metrics?.niveis?.n3?.resolvidos || 0) + (metrics?.niveis?.n4?.resolvidos || 0),
    total: 0
  };

  totalGeral.total = totalGeral.novos + totalGeral.progresso + totalGeral.pendentes + totalGeral.resolvidos;

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-[#5A9BD4] text-white p-4 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-6">
          <Button variant="ghost" size="sm" className="text-white hover:bg-blue-600">
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-xl font-semibold">Dashboard GLPI</h1>
            <p className="text-sm text-blue-100">Departamento de Tecnologia do Estado</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-white/20 rounded-lg px-4 py-2 w-80">
            <Search className="w-4 h-4 text-white/80" />
            <Input 
              placeholder="Buscar chamados... (Ctrl+K)" 
              className="bg-transparent border-none text-white placeholder:text-white/70 flex-1"
            />
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            className="text-white hover:bg-blue-600"
            onClick={handleRefresh}
            disabled={metricsLoading}
          >
            <RotateCcw className={`w-4 h-4 ${metricsLoading ? 'animate-spin' : ''}`} />
          </Button>
          <Button variant="ghost" size="sm" className="text-white hover:bg-blue-600 relative">
            <Bell className="w-4 h-4" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </Button>
          <Button variant="ghost" size="sm" className="text-white hover:bg-blue-600">
            <Settings className="w-4 h-4" />
          </Button>
          <div className="flex items-center gap-3 ml-4 pl-4 border-l border-white/20">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="text-sm">
              <p className="text-white font-medium">Admin</p>
              <p className="text-blue-100 text-xs">
                {currentTime.toLocaleTimeString('pt-BR')}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="p-6 bg-gray-100 h-[calc(100vh-80px)] overflow-hidden">
        <div className="flex gap-6 h-full">
          {/* Left Column - Dashboard Stats */}
          <div className="flex-1 flex flex-col max-w-[calc(100%-22rem)]">
            {/* Stats Cards */}
            <div className="grid grid-cols-4 gap-4 mb-4">
              <Card className="bg-white border-l-4 border-l-[#5A9BD4] shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Novos</p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {totalGeral.novos}
                      </p>
                    </div>
                    <div className="w-10 h-10 bg-[#5A9BD4]/10 rounded-lg flex items-center justify-center">
                      <TrendingUp className="w-5 h-5 text-[#5A9BD4]" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white border-l-4 border-l-orange-500 shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Em Progresso</p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {totalGeral.progresso}
                      </p>
                    </div>
                    <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                      <AlertTriangle className="w-5 h-5 text-orange-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white border-l-4 border-l-amber-500 shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Pendentes</p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {totalGeral.pendentes}
                      </p>
                    </div>
                    <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                      <Clock className="w-5 h-5 text-amber-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white border-l-4 border-l-green-500 shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Resolvidos</p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {formatNumber(totalGeral.resolvidos)}
                      </p>
                    </div>
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Level Stats - 2x2 Grid */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              {/* Nível N1 */}
              <Card className="bg-white shadow-sm border-0">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-[#5A9BD4] text-sm">
                      <Activity className="w-4 h-4" />
                      Nível N1
                    </span>
                    <span className="text-xl font-semibold text-gray-900">
                      {metrics?.niveis?.n1?.total || 0}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-[#5A9BD4] rounded-full"></span>
                        Novos
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n1?.novos || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                        Em Progr.
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n1?.progresso || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex igatems-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                        Pendentes
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n1?.pendentes || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Resolvidos
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n1?.resolvidos || 0}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Nível N2 */}
              <Card className="bg-white shadow-sm border-0">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-[#5A9BD4] text-sm">
                      <Activity className="w-4 h-4" />
                      Nível N2
                    </span>
                    <span className="text-xl font-semibold text-gray-900">
                      {metrics?.niveis?.n2?.total || 0}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-[#5A9BD4] rounded-full"></span>
                        Novos
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n2?.novos || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                        Em Progr.
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n2?.progresso || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                        Pendentes
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n2?.pendentes || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Resolvidos
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n2?.resolvidos || 0}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Nível N3 */}
              <Card className="bg-white shadow-sm border-0">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-[#5A9BD4] text-sm">
                      <Activity className="w-4 h-4" />
                      Nível N3
                    </span>
                    <span className="text-xl font-semibold text-gray-900">
                      {metrics?.niveis?.n3?.total || 0}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-[#5A9BD4] rounded-full"></span>
                        Novos
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n3?.novos || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                        Em Progr.
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n3?.progresso || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                        Pendentes
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n3?.pendentes || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Resolvidos
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n3?.resolvidos || 0}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Nível N4 */}
              <Card className="bg-white shadow-sm border-0">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-[#5A9BD4] text-sm">
                      <Activity className="w-4 h-4" />
                      Nível N4
                    </span>
                    <span className="text-xl font-semibold text-gray-900">
                      {metrics?.niveis?.n4?.total || 0}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-[#5A9BD4] rounded-full"></span>
                        Novos
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n4?.novos || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                        Em Progr.
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n4?.progresso || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                        Pendentes
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n4?.pendentes || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Resolvidos
                      </span>
                      <span className="font-medium text-gray-900 text-sm">
                        {metrics?.niveis?.n4?.resolvidos || 0}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Ranking de Técnicos */}
            <Card className="bg-white shadow-sm border-0 flex-1">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-lg">
                  <Award className="w-5 h-5" />
                  Ranking de Técnicos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-3">
                  {rankingLoading && !ranking?.length ? (
                    <div className="col-span-4 text-center py-4">
                      <Loader2 className="w-6 h-6 text-[#5A9BD4] animate-spin mx-auto" />
                      <p className="text-sm text-gray-500 mt-2">Carregando ranking...</p>
                    </div>
                  ) : ranking?.length > 0 ? (
                    ranking.slice(0, 4).map((tech, index) => {
                      const gradientClass = index === 0 
                        ? "from-[#5A9BD4] to-[#4A8BC2]" 
                        : index === 1 
                        ? "from-slate-600 to-slate-700"
                        : index === 2
                        ? "from-orange-600 to-orange-700"
                        : "from-[#5A9BD4] to-[#4A8BC2]";
                      
                      const badgeClass = index === 0
                        ? "bg-yellow-500 text-yellow-900"
                        : index === 1
                        ? "bg-gray-300 text-gray-800"
                        : index === 2
                        ? "bg-orange-200 text-orange-900"
                        : "bg-blue-200 text-blue-900";

                      const textColor = index === 1 
                        ? "text-slate-200"
                        : index === 2
                        ? "text-orange-100"
                        : "text-blue-100";

                      return (
                        <div key={tech.id || index} className={`bg-gradient-to-br ${gradientClass} text-white p-3 rounded-lg shadow-sm`}>
                          <div className="text-center">
                            <Badge className={`${badgeClass} mb-2 font-medium text-xs`}>
                              #{index + 1}
                            </Badge>
                            <p className="text-xs font-medium mb-1 truncate">
                              {tech.name || tech.nome || 'Técnico'}
                            </p>
                            <p className={`text-xs ${textColor} mb-2 truncate`}>
                              {tech.level || 'N1'}
                            </p>
                            <div className="space-y-1">
                              <div className="text-xs">
                                <span className={textColor}>Total:</span>
                                <span className="font-medium ml-1">{tech.total || 0}</span>
                              </div>
                              <div className="text-xs">
                                <span className={textColor}>Resolvidos:</span>
                                <span className="font-medium ml-1">
                                  {tech.ticketsResolved || Math.floor((tech.total || 0) * 0.95)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="col-span-4 text-center py-4 text-gray-500">
                      <p className="text-sm">Nenhum técnico encontrado</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Tickets */}
          <div className="w-[22rem]">
            <Card className="bg-white shadow-sm border-0 h-full flex flex-col">
              <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-lg">
                    <Ticket className="w-5 h-5" />
                    Tickets Novos
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded-md">
                      {tickets?.length || 0} tickets
                    </span>
                    <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700 hover:bg-gray-100">
                      <RotateCcw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden p-0">
                <div 
                  className="h-full overflow-y-auto px-6 pb-6 [&::-webkit-scrollbar]:w-[6px] [&::-webkit-scrollbar-track]:bg-slate-100 [&::-webkit-scrollbar-track]:rounded-sm [&::-webkit-scrollbar-thumb]:bg-[#5A9BD4] [&::-webkit-scrollbar-thumb]:rounded-sm [&::-webkit-scrollbar-thumb:hover]:bg-[#4A8BC2]" 
                  style={{
                    scrollbarWidth: 'thin',
                    scrollbarColor: '#5A9BD4 #f1f5f9'
                  }}
                >
                  <div className="space-y-3">
                    {ticketsLoading && !tickets?.length ? (
                      <div className="text-center py-4">
                        <Loader2 className="w-6 h-6 text-[#5A9BD4] animate-spin mx-auto" />
                        <p className="text-sm text-gray-500 mt-2">Carregando tickets...</p>
                      </div>
                    ) : tickets?.length > 0 ? (
                      tickets.map((ticket) => (
                        <div key={ticket.id} className="border-l-4 border-[#5A9BD4] bg-[#5A9BD4]/5 p-3 rounded-r-lg">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              #{ticket.id}
                            </span>
                            <Badge variant="outline" className="border-[#5A9BD4] text-[#5A9BD4] bg-[#5A9BD4]/10 text-xs">
                              {ticket.status || 'Nova'}
                            </Badge>
                          </div>
                          <h4 className="font-medium text-gray-900 mb-2 text-sm line-clamp-2">
                            {ticket.title}
                          </h4>
                          <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                            {ticket.description}
                          </p>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-700 font-medium truncate max-w-[150px]">
                              {ticket.requester}
                            </span>
                            <span className="text-gray-500">
                              {formatDate(ticket.date)}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-4 text-gray-500">
                        <p className="text-sm">Nenhum ticket novo</p>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}