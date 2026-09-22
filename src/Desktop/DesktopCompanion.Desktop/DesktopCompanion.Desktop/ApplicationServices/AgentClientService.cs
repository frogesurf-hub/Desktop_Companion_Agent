using System.Collections.Concurrent;
using System.Text.Json.Nodes;

using DesktopCompanion.Desktop.Communication;
using DesktopCompanion.Desktop.Protocol;

namespace DesktopCompanion.Desktop.ApplicationServices;

public sealed class AgentClientService : IAgentClientService
{
    private readonly IAgentConnection _connection;

    private CancellationTokenSource? _receiveCancellation;
    private readonly ConcurrentDictionary<
        string,
        TaskCompletionSource<AgentMessage>>
        _pendingRequests =
            new(StringComparer.Ordinal);

    private readonly SemaphoreSlim _sendGate = new(
        initialCount: 1,
        maxCount: 1);
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

    public async Task SendChatAsync(
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

        await SendMessageAsync(
            request,
            cancellationToken)
            .ConfigureAwait(false);
    }

    public async Task<AgentMessage> SendRequestAsync(
        AgentMessage request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(
            request);

        if (!IsConnected)
        {
            throw new InvalidOperationException(
                "The Agent connection is not open.");
        }

        if (string.IsNullOrWhiteSpace(
            request.Id))
        {
            throw new ArgumentException(
                "Request ID cannot be empty.",
                nameof(request));
        }

        var completion =
            new TaskCompletionSource<AgentMessage>(
                TaskCreationOptions.RunContinuationsAsynchronously);

        if (!_pendingRequests.TryAdd(
            request.Id,
            completion))
        {
            throw new InvalidOperationException(
                "A request with the same ID is already pending.");
        }

        using CancellationTokenRegistration registration =
            cancellationToken.Register(
                () =>
                {
                    if (_pendingRequests.TryRemove(
                        request.Id,
                        out TaskCompletionSource<
                            AgentMessage>? pending))
                    {
                        pending.TrySetCanceled(
                            cancellationToken);
                    }
                });

        try
        {
            await SendMessageAsync(
                request,
                cancellationToken)
                .ConfigureAwait(false);

            return await completion.Task
                .ConfigureAwait(false);
        }
        catch
        {
            _pendingRequests.TryRemove(
                request.Id,
                out _);

            throw;
        }
    }

    public async Task DisconnectAsync(
        CancellationToken cancellationToken = default)
    {
        _receiveCancellation?.Cancel();

        CancelPendingRequests();

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

        try
        {
            await _connection.DisconnectAsync(
                cancellationToken);
        }
        finally
        {
            CancelPendingRequests();

            _receiveCancellation?.Dispose();

            _receiveCancellation = null;
            _receiveTask = null;
        }
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

                if (TryGetRequestId(
                    message,
                    out string requestId))
                {
                    if (_pendingRequests.TryRemove(
                        requestId,
                        out TaskCompletionSource<
                            AgentMessage>? completion))
                    {
                        completion.TrySetResult(
                            message);
                    }

                    continue;
                }

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
            FailPendingRequests(
                exception);

            ReceiveFailed?.Invoke(
                exception);
        }
    }

    private async Task SendMessageAsync(
        AgentMessage message,
        CancellationToken cancellationToken)
    {
        await _sendGate.WaitAsync(
            cancellationToken)
            .ConfigureAwait(false);

        try
        {
            await _connection.SendAsync(
                message,
                cancellationToken)
                .ConfigureAwait(false);
        }
        finally
        {
            _sendGate.Release();
        }
    }

    private static bool TryGetRequestId(
        AgentMessage message,
        out string requestId)
    {
        requestId = string.Empty;

        if (!message.Payload.TryGetPropertyValue(
                "request_id",
                out JsonNode? node) ||
            node is not JsonValue value ||
            !value.TryGetValue<string>(
                out string? candidate) ||
            string.IsNullOrWhiteSpace(
                candidate))
        {
            return false;
        }

        requestId = candidate;

        return true;
    }


    private void CancelPendingRequests()
    {
        foreach (
            KeyValuePair<
                string,
                TaskCompletionSource<AgentMessage>>
            item in _pendingRequests)
        {
            if (_pendingRequests.TryRemove(
                item.Key,
                out TaskCompletionSource<
                    AgentMessage>? completion))
            {
                completion.TrySetCanceled();
            }
        }
    }


    private void FailPendingRequests(
        Exception exception)
    {
        foreach (
            KeyValuePair<
                string,
                TaskCompletionSource<AgentMessage>>
            item in _pendingRequests)
        {
            if (_pendingRequests.TryRemove(
                item.Key,
                out TaskCompletionSource<
                    AgentMessage>? completion))
            {
                completion.TrySetException(
                    exception);
            }
        }
    }
}
