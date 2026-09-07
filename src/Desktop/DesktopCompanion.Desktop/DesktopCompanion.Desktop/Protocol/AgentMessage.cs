using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace DesktopCompanion.Desktop.Protocol;

public sealed class AgentMessage
{
    [JsonPropertyName("id")]
    public required string Id { get; init; }

    [JsonPropertyName("type")]
    public required string Type { get; init; }

    [JsonPropertyName("timestamp")]
    public required string Timestamp { get; init; }

    [JsonPropertyName("source")]
    public required string Source { get; init; }

    [JsonPropertyName("payload")]
    public required JsonObject Payload { get; init; }

    public static AgentMessage Create(
        string type,
        string source,
        JsonObject payload)
    {
        return new AgentMessage
        {
            Id = Guid.NewGuid().ToString(),
            Type = type,
            Timestamp = DateTimeOffset.UtcNow.ToString("O"),
            Source = source,
            Payload = payload,
        };
    }
}
