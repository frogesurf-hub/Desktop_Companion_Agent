using DesktopCompanion.Desktop.Protocol;

namespace DesktopCompanion.Desktop.Communication;

public interface IAgentConnection : IAsyncDisposable
{
    bool IsConnected { get; }

    Task ConnectAsync(
        Uri endpoint,
        CancellationToken cancellationToken = default);

    Task DisconnectAsync(
        CancellationToken cancellationToken = default);

    Task SendAsync(
        AgentMessage message,
        CancellationToken cancellationToken = default);

    Task<AgentMessage> ReceiveAsync(
        CancellationToken cancellationToken = default);
}
