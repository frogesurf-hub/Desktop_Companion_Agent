using System.Text.Json.Serialization;

namespace DesktopCompanion.Desktop.Protocol;

public sealed class MemoryScopePayload
{
    [JsonPropertyName("kind")]
    public required string Kind { get; init; }

    [JsonPropertyName("character_id")]
    [JsonIgnore(
        Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? CharacterId { get; init; }
}

public sealed class MemoryRevisionPayload
{
    [JsonPropertyName("revision_number")]
    public required int RevisionNumber { get; init; }

    [JsonPropertyName("content")]
    public string? Content { get; init; }

    [JsonPropertyName("source")]
    public required string Source { get; init; }

    [JsonPropertyName("lifecycle")]
    public required string Lifecycle { get; init; }

    [JsonPropertyName("recorded_at")]
    public required string RecordedAt { get; init; }

    [JsonPropertyName("occurred_at")]
    public string? OccurredAt { get; init; }
}

public sealed class MemoryEntryPayload
{
    [JsonPropertyName("memory_id")]
    public required string MemoryId { get; init; }

    [JsonPropertyName("domain")]
    public required string Domain { get; init; }

    [JsonPropertyName("scope")]
    public required MemoryScopePayload Scope { get; init; }

    [JsonPropertyName("identity_key")]
    public string? IdentityKey { get; init; }

    [JsonPropertyName("latest_revision")]
    public required MemoryRevisionPayload LatestRevision { get; init; }
}

public sealed class MemoryListRequestPayload
{
    [JsonPropertyName("domain")]
    [JsonIgnore(
        Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Domain { get; init; }

    [JsonPropertyName("scope")]
    [JsonIgnore(
        Condition = JsonIgnoreCondition.WhenWritingNull)]
    public MemoryScopePayload? Scope { get; init; }
}

public sealed class MemoryIdRequestPayload
{
    [JsonPropertyName("memory_id")]
    public required string MemoryId { get; init; }
}

public sealed class MemoryEditRequestPayload
{
    [JsonPropertyName("memory_id")]
    public required string MemoryId { get; init; }

    [JsonPropertyName("content")]
    public required string Content { get; init; }
}

public sealed class MemoryListResultPayload
{
    [JsonPropertyName("request_id")]
    public required string RequestId { get; init; }

    [JsonPropertyName("memories")]
    public required List<MemoryEntryPayload> Memories { get; init; }
}

public sealed class MemoryEntryResultPayload
{
    [JsonPropertyName("request_id")]
    public required string RequestId { get; init; }

    [JsonPropertyName("memory")]
    public required MemoryEntryPayload Memory { get; init; }
}

public sealed class MemoryHistoryResultPayload
{
    [JsonPropertyName("request_id")]
    public required string RequestId { get; init; }

    [JsonPropertyName("memory_id")]
    public required string MemoryId { get; init; }

    [JsonPropertyName("revisions")]
    public required List<MemoryRevisionPayload> Revisions { get; init; }
}

public sealed class MemoryErrorPayload
{
    [JsonPropertyName("request_id")]
    public required string RequestId { get; init; }

    [JsonPropertyName("code")]
    public required string Code { get; init; }

    [JsonPropertyName("message")]
    public required string Message { get; init; }
}
