using System.Text.Json.Nodes;

using DesktopCompanion.Desktop.Communication;
using DesktopCompanion.Desktop.Protocol;

namespace DesktopCompanion.Desktop.ApplicationServices;

public sealed class AgentClientService : IAgentClientService
{
    private readonly IAgentConnection _connection;

    private CancellationTokenSource? _receiveCancellation;
    private Task? _receiveTask;

    public AgentClientService(
        IAgentConnection connection)
    {
        _connection = connection;
    }

    public bool IsConnected =>
        _connection.IsConnected;

    public event Action<AgentMessage>? MessageReceived;

    public event Action<Exception>? ReceiveFailed;

    public async Task ConnectAsync(
        Uri endpoint,
        CancellationToken cancellationToken = default)
    {
        if (IsConnected)
        {
            return;
        }

        await _connection.ConnectAsync(
            endpoint,
            cancellationToken);

        _receiveCancellation =
            new CancellationTokenSource();

        _receiveTask = ReceiveLoopAsync(
            _receiveCancellation.Token);
    }

    public Task SendChatAsync(
        string message,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(message))
        {
            throw new ArgumentException(
                "Chat message cannot be empty.",
                nameof(message));
        }

        AgentMessage request = AgentMessage.Create(
            type: "chat",
            source: "desktop",
            payload: new JsonObject
            {
                ["message"] = message,
            });

        return _connection.SendAsync(
            request,
            cancellationToken);
    }

    public async Task DisconnectAsync(
        CancellationToken cancellationToken = default)
    {
        _receiveCancellation?.Cancel();

        if (_receiveTask is not null)
        {
            try
            {
                await _receiveTask;
            }
            catch (OperationCanceledException)
            {
                // Expected during a normal disconnect.
            }
        }

        await _connection.DisconnectAsync(
            cancellationToken);

        _receiveCancellation?.Dispose();

        _receiveCancellation = null;
        _receiveTask = null;
    }

    public async ValueTask DisposeAsync()
    {
        await DisconnectAsync();
        await _connection.DisposeAsync();

        GC.SuppressFinalize(this);
    }

    private async Task ReceiveLoopAsync(
        CancellationToken cancellationToken)
    {
        try
        {
            while (
                !cancellationToken.IsCancellationRequested &&
                _connection.IsConnected)
            {
                AgentMessage message =
                    await _connection.ReceiveAsync(
                        cancellationToken)
                    .ConfigureAwait(false);

                MessageReceived?.Invoke(
                    message);
            }
        }
        catch (OperationCanceledException)
            when (cancellationToken.IsCancellationRequested)
        {
            // Normal shutdown of the receive loop.
        }
        catch (Exception exception)
        {
            ReceiveFailed?.Invoke(
                exception);
        }
    }
}
