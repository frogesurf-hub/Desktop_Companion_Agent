using System.Text.Json;
using System.Text.Json.Nodes;

namespace DesktopCompanion.Desktop.Protocol;

public static class MemoryProtocol
{
    private const string DesktopSource = "desktop";

    private static readonly HashSet<string>
        SupportedDomains =
            new(StringComparer.Ordinal)
            {
                Domains.UserProfile,
                Domains.WorkingContext,
                Domains.Episodic,
                Domains.Relationship,
            };

    public static class MessageTypes
    {
        public const string List = "memory.list";
        public const string Inspect = "memory.inspect";
        public const string Edit = "memory.edit";
        public const string Delete = "memory.delete";
        public const string History = "memory.history";

        public const string ListResult =
            "memory.list.result";

        public const string InspectResult =
            "memory.inspect.result";

        public const string EditResult =
            "memory.edit.result";

        public const string DeleteResult =
            "memory.delete.result";

        public const string HistoryResult =
            "memory.history.result";

        public const string Error = "error";
    }

    public static class Domains
    {
        public const string UserProfile =
            "user_profile";

        public const string WorkingContext =
            "working_context";

        public const string Episodic =
            "episodic";

        public const string Relationship =
            "relationship";
    }

    public static class ScopeKinds
    {
        public const string GlobalUser =
            "global_user";

        public const string Character =
            "character";
    }

    public static class Lifecycles
    {
        public const string Active = "active";

        public const string Superseded =
            "superseded";

        public const string Expired = "expired";

        public const string Deleted = "deleted";
    }

    public static class Sources
    {
        public const string UserEdit =
            "user_edit";

        public const string UserExplicit =
            "user_explicit";

        public const string AutomaticExplicitFact =
            "automatic_explicit_fact";

        public const string SystemObserved =
            "system_observed";
    }

    public static class ErrorCodes
    {
        public const string InvalidRequest =
            "MEMORY_INVALID_REQUEST";

        public const string NotFound =
            "MEMORY_NOT_FOUND";

        public const string Deleted =
            "MEMORY_DELETED";

        public const string InvalidState =
            "MEMORY_INVALID_STATE";

        public const string OperationFailed =
            "MEMORY_OPERATION_FAILED";
    }

    public static MemoryScopePayload
        CreateGlobalUserScope()
    {
        return new MemoryScopePayload
        {
            Kind = ScopeKinds.GlobalUser,
        };
    }

    public static MemoryScopePayload
        CreateCharacterScope(
            string characterId)
    {
        if (string.IsNullOrWhiteSpace(
            characterId))
        {
            throw new ArgumentException(
                "Character ID cannot be empty.",
                nameof(characterId));
        }

        return new MemoryScopePayload
        {
            Kind = ScopeKinds.Character,
            CharacterId = characterId,
        };
    }

    public static AgentMessage CreateListRequest(
        string? domain = null,
        MemoryScopePayload? scope = null)
    {
        if (
            domain is not null &&
            !SupportedDomains.Contains(domain))
        {
            throw new ArgumentException(
                "Unsupported Memory domain.",
                nameof(domain));
        }

        ValidateScope(
            scope);

        ValidateDomainScopePair(
            domain,
            scope);

        return CreateRequest(
            MessageTypes.List,
            new MemoryListRequestPayload
            {
                Domain = domain,
                Scope = scope,
            });
    }

    public static AgentMessage CreateInspectRequest(
        string memoryId)
    {
        return CreateRequest(
            MessageTypes.Inspect,
            new MemoryIdRequestPayload
            {
                MemoryId = NormalizeMemoryId(
                    memoryId),
            });
    }

    public static AgentMessage CreateEditRequest(
        string memoryId,
        string content)
    {
        if (string.IsNullOrWhiteSpace(
            content))
        {
            throw new ArgumentException(
                "Memory content cannot be empty.",
                nameof(content));
        }

        return CreateRequest(
            MessageTypes.Edit,
            new MemoryEditRequestPayload
            {
                MemoryId = NormalizeMemoryId(
                    memoryId),
                Content = content,
            });
    }

    public static AgentMessage CreateDeleteRequest(
        string memoryId)
    {
        return CreateRequest(
            MessageTypes.Delete,
            new MemoryIdRequestPayload
            {
                MemoryId = NormalizeMemoryId(
                    memoryId),
            });
    }

    public static AgentMessage CreateHistoryRequest(
        string memoryId)
    {
        return CreateRequest(
            MessageTypes.History,
            new MemoryIdRequestPayload
            {
                MemoryId = NormalizeMemoryId(
                    memoryId),
            });
    }

    public static MemoryListResultPayload
        ParseListResult(
            AgentMessage message)
    {
        return ParsePayload<
            MemoryListResultPayload>(
                message,
                MessageTypes.ListResult);
    }

    public static MemoryEntryResultPayload
        ParseInspectResult(
            AgentMessage message)
    {
        return ParsePayload<
            MemoryEntryResultPayload>(
                message,
                MessageTypes.InspectResult);
    }

    public static MemoryEntryResultPayload
        ParseEditResult(
            AgentMessage message)
    {
        return ParsePayload<
            MemoryEntryResultPayload>(
                message,
                MessageTypes.EditResult);
    }

    public static MemoryEntryResultPayload
        ParseDeleteResult(
            AgentMessage message)
    {
        return ParsePayload<
            MemoryEntryResultPayload>(
                message,
                MessageTypes.DeleteResult);
    }

    public static MemoryHistoryResultPayload
        ParseHistoryResult(
            AgentMessage message)
    {
        return ParsePayload<
            MemoryHistoryResultPayload>(
                message,
                MessageTypes.HistoryResult);
    }

    public static MemoryErrorPayload ParseError(
        AgentMessage message)
    {
        return ParsePayload<
            MemoryErrorPayload>(
                message,
                MessageTypes.Error);
    }

    private static AgentMessage CreateRequest<T>(
        string type,
        T payload)
    {
        JsonNode? payloadNode =
            JsonSerializer.SerializeToNode(
                payload);

        if (payloadNode is not JsonObject payloadObject)
        {
            throw new JsonException(
                "Memory request payload "
                + "must serialize to an object.");
        }

        return AgentMessage.Create(
            type: type,
            source: DesktopSource,
            payload: payloadObject);
    }

    private static T ParsePayload<T>(
        AgentMessage message,
        string expectedType)
        where T : class
    {
        if (!string.Equals(
            message.Type,
            expectedType,
            StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"Expected protocol message "
                + $"type '{expectedType}', "
                + $"but received '{message.Type}'.");
        }

        T? payload =
            message.Payload.Deserialize<T>();

        if (payload is null)
        {
            throw new JsonException(
                "Memory protocol payload "
                + "could not be deserialized.");
        }

        return payload;
    }

    private static string NormalizeMemoryId(
        string memoryId)
    {
        if (
            string.IsNullOrWhiteSpace(memoryId) ||
            !Guid.TryParse(
                memoryId,
                out Guid parsed))
        {
            throw new ArgumentException(
                "Memory ID must be a valid UUID.",
                nameof(memoryId));
        }

        return parsed.ToString();
    }

    private static void ValidateDomainScopePair(
        string? domain,
        MemoryScopePayload? scope)
    {
        if (domain is null || scope is null)
        {
            return;
        }

        string requiredScopeKind =
            domain == Domains.Relationship
                ? ScopeKinds.Character
                : ScopeKinds.GlobalUser;

        if (!string.Equals(
            scope.Kind,
            requiredScopeKind,
            StringComparison.Ordinal))
        {
            throw new ArgumentException(
                "Memory domain and scope are incompatible.");
        }
    }

    private static void ValidateScope(
        MemoryScopePayload? scope)
    {
        if (scope is null)
        {
            return;
        }

        if (scope.Kind == ScopeKinds.GlobalUser)
        {
            if (scope.CharacterId is not null)
            {
                throw new ArgumentException(
                    "Global-user Memory scope "
                    + "cannot define a Character ID.",
                    nameof(scope));
            }

            return;
        }

        if (scope.Kind == ScopeKinds.Character)
        {
            if (string.IsNullOrWhiteSpace(
                scope.CharacterId))
            {
                throw new ArgumentException(
                    "Character Memory scope "
                    + "requires a Character ID.",
                    nameof(scope));
            }

            return;
        }

        throw new ArgumentException(
            "Unsupported Memory scope kind.",
            nameof(scope));
    }
}
