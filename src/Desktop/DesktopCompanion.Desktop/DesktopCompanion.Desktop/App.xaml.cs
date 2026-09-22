using System.Windows;

using DesktopCompanion.Desktop.ApplicationServices;
using DesktopCompanion.Desktop.Communication;
using DesktopCompanion.Desktop.Presentation;

namespace DesktopCompanion.Desktop;

public partial class App : System.Windows.Application
{
    protected override void OnStartup(
        StartupEventArgs e)
    {
        base.OnStartup(e);

        IAgentConnection connection =
            new WebSocketAgentConnection();

        IAgentClientService agentClientService =
            new AgentClientService(
                connection);

        IMemoryClientService memoryClientService =
            new MemoryClientService(
                agentClientService);

        var memoryViewModel =
            new MemoryManagementViewModel(
                memoryClientService);

        var viewModel =
            new MainWindowViewModel(
                agentClientService,
                memoryViewModel,
                new Uri(
                    "ws://127.0.0.1:8765"));

        var window =
            new MainWindow(
                viewModel);

        MainWindow = window;

        window.Show();
    }
}
