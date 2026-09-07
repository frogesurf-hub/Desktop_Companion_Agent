using DesktopCompanion.Desktop.Protocol;
using System.IO;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;

namespace DesktopCompanion.Desktop.Communication;

public sealed class WebSocketAgentConnection : IAgentConnection
{
    private const int ReceiveBufferSize = 4096;

    private ClientWebSocket? _webSocket;

    public bool IsConnected =>
        _webSocket?.State == WebSocketState.Open;

    public async Task ConnectAsync(
        Uri endpoint,
        CancellationToken cancellationToken = default)
    {
        if (IsConnected)
        {
            return;
        }

        await DisposeSocketAsync();

        _webSocket = new ClientWebSocket();

        await _webSocket.ConnectAsync(
            endpoint,
            cancellationToken);
    }

    public async Task DisconnectAsync(
        CancellationToken cancellationToken = default)
    {
        if (_webSocket is null)
        {
            return;
        }

        if (_webSocket.State == WebSocketState.Open)
        {
            await _webSocket.CloseAsync(
                WebSocketCloseStatus.NormalClosure,
                "Desktop client disconnecting",
                cancellationToken);
        }

        await DisposeSocketAsync();
    }

    public async Task SendAsync(
        AgentMessage message,
        CancellationToken cancellationToken = default)
    {
        ClientWebSocket webSocket = GetOpenSocket();

        string json = JsonSerializer.Serialize(
            message);

        byte[] data = Encoding.UTF8.GetBytes(
            json);

        await webSocket.SendAsync(
            new ArraySegment<byte>(data),
            WebSocketMessageType.Text,
            endOfMessage: true,
            cancellationToken);
    }

    public async Task<AgentMessage> ReceiveAsync(
        CancellationToken cancellationToken = default)
    {
        ClientWebSocket webSocket = GetOpenSocket();

        byte[] buffer = new byte[ReceiveBufferSize];

        using var stream = new MemoryStream();

        WebSocketReceiveResult result;

        do
        {
            result = await webSocket.ReceiveAsync(
                new ArraySegment<byte>(buffer),
                cancellationToken);

            if (result.MessageType == WebSocketMessageType.Close)
            {
                throw new WebSocketException(
                    "The Agent Core closed the WebSocket connection.");
            }

            stream.Write(
                buffer,
                0,
                result.Count);
        }
        while (!result.EndOfMessage);

        string json = Encoding.UTF8.GetString(
            stream.ToArray());

        AgentMessage? message =
            JsonSerializer.Deserialize<AgentMessage>(
                json);

        if (message is null)
        {
            throw new JsonException(
                "Received an empty or invalid AgentMessage.");
        }

        return message;
    }

    public async ValueTask DisposeAsync()
    {
        await DisposeSocketAsync();
        GC.SuppressFinalize(this);
    }

    private ClientWebSocket GetOpenSocket()
    {
        if (_webSocket is null ||
            _webSocket.State != WebSocketState.Open)
        {
            throw new InvalidOperationException(
                "The Agent connection is not open.");
        }

        return _webSocket;
    }

    private ValueTask DisposeSocketAsync()
    {
        _webSocket?.Dispose();
        _webSocket = null;

        return ValueTask.CompletedTask;
    }
}
