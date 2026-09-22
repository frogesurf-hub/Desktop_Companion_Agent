using DesktopCompanion.Desktop.Protocol;

namespace DesktopCompanion.Desktop.ApplicationServices;

public sealed class MemoryClientService : IMemoryClientService
{
    private readonly IAgentClientService _agentClientService;

    public MemoryClientService(
        IAgentClientService agentClientService)
    {
        ArgumentNullException.ThrowIfNull(
            agentClientService);

        _agentClientService = agentClientService;
    }

    public bool IsConnected =>
        _agentClientService.IsConnected;

    public async Task<
        IReadOnlyList<MemoryEntryPayload>> ListAsync(
        string? domain = null,
        MemoryScopePayload? scope = null,
        CancellationToken cancellationToken = default)
    {
        AgentMessage request =
            MemoryProtocol.CreateListRequest(
                domain,
                scope);

        AgentMessage response =
            await SendMemoryRequestAsync(
                request,
                MemoryProtocol.MessageTypes.ListResult,
                cancellationToken)
            .ConfigureAwait(false);

        MemoryListResultPayload result =
            MemoryProtocol.ParseListResult(
                response);

        return result.Memories;
    }

    public async Task<MemoryEntryPayload> InspectAsync(
        string memoryId,
        CancellationToken cancellationToken = default)
    {
        AgentMessage request =
            MemoryProtocol.CreateInspectRequest(
                memoryId);

        AgentMessage response =
            await SendMemoryRequestAsync(
                request,
                MemoryProtocol.MessageTypes.InspectResult,
                cancellationToken)
            .ConfigureAwait(false);

        return MemoryProtocol.ParseInspectResult(
            response)
            .Memory;
    }

    public async Task<MemoryEntryPayload> EditAsync(
        string memoryId,
        string content,
        CancellationToken cancellationToken = default)
    {
        AgentMessage request =
            MemoryProtocol.CreateEditRequest(
                memoryId,
                content);

        AgentMessage response =
            await SendMemoryRequestAsync(
                request,
                MemoryProtocol.MessageTypes.EditResult,
                cancellationToken)
            .ConfigureAwait(false);

        return MemoryProtocol.ParseEditResult(
            response)
            .Memory;
    }

    public async Task<MemoryEntryPayload> DeleteAsync(
        string memoryId,
        CancellationToken cancellationToken = default)
    {
        AgentMessage request =
            MemoryProtocol.CreateDeleteRequest(
                memoryId);

        AgentMessage response =
            await SendMemoryRequestAsync(
                request,
                MemoryProtocol.MessageTypes.DeleteResult,
                cancellationToken)
            .ConfigureAwait(false);

        return MemoryProtocol.ParseDeleteResult(
            response)
            .Memory;
    }

    public async Task<
        IReadOnlyList<MemoryRevisionPayload>> GetHistoryAsync(
        string memoryId,
        CancellationToken cancellationToken = default)
    {
        AgentMessage request =
            MemoryProtocol.CreateHistoryRequest(
                memoryId);

        AgentMessage response =
            await SendMemoryRequestAsync(
                request,
                MemoryProtocol.MessageTypes.HistoryResult,
                cancellationToken)
            .ConfigureAwait(false);

        MemoryHistoryResultPayload result =
            MemoryProtocol.ParseHistoryResult(
                response);

        return result.Revisions;
    }

    private async Task<AgentMessage> SendMemoryRequestAsync(
        AgentMessage request,
        string expectedResponseType,
        CancellationToken cancellationToken)
    {
        AgentMessage response =
            await _agentClientService.SendRequestAsync(
                request,
                cancellationToken)
            .ConfigureAwait(false);

        if (response.Type == MemoryProtocol.MessageTypes.Error)
        {
            MemoryErrorPayload error =
                MemoryProtocol.ParseError(
                    response);

            throw new MemoryClientException(
                error.Code,
                error.Message);
        }

        if (!string.Equals(
            response.Type,
            expectedResponseType,
            StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"Expected Memory response type "
                + $"'{expectedResponseType}', "
                + $"but received '{response.Type}'.");
        }

        return response;
    }
}
