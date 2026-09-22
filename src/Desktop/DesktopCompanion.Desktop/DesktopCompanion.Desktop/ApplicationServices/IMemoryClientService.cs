using DesktopCompanion.Desktop.Protocol;

namespace DesktopCompanion.Desktop.ApplicationServices;

public interface IMemoryClientService
{
    bool IsConnected { get; }

    Task<IReadOnlyList<MemoryEntryPayload>> ListAsync(
        string? domain = null,
        MemoryScopePayload? scope = null,
        CancellationToken cancellationToken = default);

    Task<MemoryEntryPayload> InspectAsync(
        string memoryId,
        CancellationToken cancellationToken = default);

    Task<MemoryEntryPayload> EditAsync(
        string memoryId,
        string content,
        CancellationToken cancellationToken = default);

    Task<MemoryEntryPayload> DeleteAsync(
        string memoryId,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<MemoryRevisionPayload>> GetHistoryAsync(
        string memoryId,
        CancellationToken cancellationToken = default);
}
