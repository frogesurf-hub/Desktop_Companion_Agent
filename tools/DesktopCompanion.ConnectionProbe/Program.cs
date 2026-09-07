using System.Text.Json.Nodes;

using DesktopCompanion.Desktop.Communication;
using DesktopCompanion.Desktop.Protocol;

var endpoint = new Uri(
    "ws://127.0.0.1:8765");

await using IAgentConnection connection =
    new WebSocketAgentConnection();

Console.WriteLine(
    $"Connecting to {endpoint}...");

await connection.ConnectAsync(
    endpoint);

Console.WriteLine(
    $"Connected: {connection.IsConnected}");

var request = AgentMessage.Create(
    type: "chat",
    source: "desktop",
    payload: new JsonObject
    {
        ["message"] = "你好",
    });

await connection.SendAsync(
    request);

Console.WriteLine(
    "Sent chat message.");

AgentMessage response =
    await connection.ReceiveAsync();

Console.WriteLine(
    $"Response type: {response.Type}");

Console.WriteLine(
    $"Response message: {response.Payload["message"]}");

await connection.DisconnectAsync();

Console.WriteLine(
    "Disconnected.");