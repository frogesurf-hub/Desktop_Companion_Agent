using DesktopCompanion.Desktop.Protocol;

namespace DesktopCompanion.Desktop.ApplicationServices;

public interface IAgentClientService : IAsyncDisposable
{
    bool IsConnected { get; }

    event Action<AgentMessage>? MessageReceived;

    event Action<Exception>? ReceiveFailed;

    Task ConnectAsync(
        Uri endpoint,
        CancellationToken cancellationToken = default);

    Task<AgentMessage> SendRequestAsync(
        AgentMessage request,
        CancellationToken cancellationToken = default);

    Task DisconnectAsync(
        CancellationToken cancellationToken = default);

    Task SendChatAsync(
        string message,
        CancellationToken cancellationToken = default);
}
