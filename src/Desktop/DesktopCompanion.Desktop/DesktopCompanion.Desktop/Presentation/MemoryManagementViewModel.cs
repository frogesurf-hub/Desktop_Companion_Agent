using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;

using DesktopCompanion.Desktop.ApplicationServices;
using DesktopCompanion.Desktop.Protocol;

namespace DesktopCompanion.Desktop.Presentation;

public sealed class MemoryManagementViewModel :
    INotifyPropertyChanged
{
    private readonly IMemoryClientService _memoryClientService;

    private MemoryEntryPayload? _selectedMemory;
    private string _selectedMemoryContent = string.Empty;

    private bool _isLoading;
    private bool _isBusy;
    private bool _hasLoaded;
    private bool _isHistoryVisible;

    private string _statusMessage =
        "Memory has not been loaded.";

    private string? _errorMessage;

    public MemoryManagementViewModel(
        IMemoryClientService memoryClientService)
    {
        ArgumentNullException.ThrowIfNull(
            memoryClientService);

        _memoryClientService =
            memoryClientService;
    }

    public event PropertyChangedEventHandler?
        PropertyChanged;

    public ObservableCollection<MemoryEntryPayload>
        Memories
    { get; } = [];

    public ObservableCollection<MemoryRevisionPayload>
        History
    { get; } = [];

    public bool IsConnected =>
        _memoryClientService.IsConnected;

    public bool IsLoading
    {
        get => _isLoading;

        private set
        {
            if (_isLoading == value)
            {
                return;
            }

            _isLoading = value;

            OnPropertyChanged();
            OnPropertyChanged(nameof(IsEmpty));
            NotifyOperationStateChanged();
        }
    }

    public bool IsBusy
    {
        get => _isBusy;

        private set
        {
            if (_isBusy == value)
            {
                return;
            }

            _isBusy = value;

            OnPropertyChanged();
            NotifyOperationStateChanged();
        }
    }

    public bool HasLoaded
    {
        get => _hasLoaded;

        private set
        {
            if (_hasLoaded == value)
            {
                return;
            }

            _hasLoaded = value;

            OnPropertyChanged();
            OnPropertyChanged(nameof(IsEmpty));
        }
    }

    public bool HasMemories =>
        Memories.Count > 0;

    public bool IsEmpty =>
        HasLoaded &&
        !IsLoading &&
        ErrorMessage is null &&
        Memories.Count == 0;

    public MemoryEntryPayload? SelectedMemory
    {
        get => _selectedMemory;

        set
        {
            if (ReferenceEquals(
                _selectedMemory,
                value))
            {
                return;
            }

            _selectedMemory = value;

            OnPropertyChanged();
            OnPropertyChanged(nameof(HasSelection));

            SelectedMemoryContent =
                value?.LatestRevision.Content
                ?? string.Empty;

            ClearHistory();

            NotifyOperationStateChanged();
        }
    }

    public bool HasSelection =>
        SelectedMemory is not null;

    public string SelectedMemoryContent
    {
        get => _selectedMemoryContent;

        set
        {
            if (_selectedMemoryContent == value)
            {
                return;
            }

            _selectedMemoryContent = value;

            OnPropertyChanged();
            OnPropertyChanged(nameof(CanSave));
        }
    }

    public bool IsHistoryVisible
    {
        get => _isHistoryVisible;

        private set
        {
            if (_isHistoryVisible == value)
            {
                return;
            }

            _isHistoryVisible = value;

            OnPropertyChanged();
        }
    }

    public string StatusMessage
    {
        get => _statusMessage;

        private set
        {
            if (_statusMessage == value)
            {
                return;
            }

            _statusMessage = value;

            OnPropertyChanged();
        }
    }

    public string? ErrorMessage
    {
        get => _errorMessage;

        private set
        {
            if (_errorMessage == value)
            {
                return;
            }

            _errorMessage = value;

            OnPropertyChanged();
            OnPropertyChanged(nameof(IsEmpty));
        }
    }

    public bool CanOperate =>
        IsConnected &&
        !IsBusy;

    public bool CanSave =>
        CanOperate &&
        HasSelection &&
        !string.IsNullOrWhiteSpace(
            SelectedMemoryContent);

    public bool CanDelete =>
        CanOperate &&
        HasSelection;

    public bool CanLoadHistory =>
        CanOperate &&
        HasSelection;

    public void RefreshConnectionState()
    {
        OnPropertyChanged(nameof(IsConnected));

        NotifyOperationStateChanged();

        if (!IsConnected)
        {
            StatusMessage =
                "Agent Core is disconnected.";
        }
    }

    public async Task LoadAsync(
        CancellationToken cancellationToken = default)
    {
        if (IsBusy ||
            !EnsureConnected())
        {
            return;
        }

        BeginOperation(
            "Loading Memory...",
            isLoading: true);

        HasLoaded = false;

        Memories.Clear();

        SelectedMemory = null;

        NotifyMemoryCollectionChanged();

        try
        {
            IReadOnlyList<MemoryEntryPayload> memories =
                await _memoryClientService.ListAsync(
                    cancellationToken:
                        cancellationToken);

            foreach (MemoryEntryPayload memory in memories)
            {
                Memories.Add(
                    memory);
            }

            HasLoaded = true;

            NotifyMemoryCollectionChanged();

            StatusMessage =
                Memories.Count == 0
                    ? "No Memory entries."
                    : $"Loaded {Memories.Count} Memory entries.";
        }
        catch (OperationCanceledException)
        {
            HandleCancellation();
        }
        catch (Exception exception)
        {
            HandleFailure(
                exception,
                "Memory load failed.");
        }
        finally
        {
            EndOperation(
                isLoading: true);
        }
    }

    public async Task InspectSelectedAsync(
        CancellationToken cancellationToken = default)
    {
        if (IsBusy ||
            !EnsureConnected() ||
            SelectedMemory is null)
        {
            return;
        }

        string memoryId =
            SelectedMemory.MemoryId;

        BeginOperation(
            "Loading Memory detail...");

        try
        {
            MemoryEntryPayload memory =
                await _memoryClientService.InspectAsync(
                    memoryId,
                    cancellationToken);

            if (!IsSelectedMemory(
                memoryId))
            {
                StatusMessage =
                    "Memory selection changed.";

                return;
            }

            ReplaceMemory(
                memory);

            SelectedMemory =
                memory;

            StatusMessage =
                "Memory detail loaded.";
        }
        catch (OperationCanceledException)
        {
            HandleCancellation();
        }
        catch (Exception exception)
        {
            HandleFailure(
                exception,
                "Memory inspection failed.");
        }
        finally
        {
            EndOperation();
        }
    }

    public async Task SaveAsync(
        CancellationToken cancellationToken = default)
    {
        if (IsBusy ||
            !EnsureConnected() ||
            SelectedMemory is null)
        {
            return;
        }

        if (string.IsNullOrWhiteSpace(
            SelectedMemoryContent))
        {
            ErrorMessage =
                "Memory content cannot be empty.";

            StatusMessage =
                "Memory edit failed.";

            return;
        }

        string memoryId =
            SelectedMemory.MemoryId;

        string content =
            SelectedMemoryContent;

        BeginOperation(
            "Saving Memory...");

        try
        {
            MemoryEntryPayload memory =
                await _memoryClientService.EditAsync(
                    memoryId,
                    content,
                    cancellationToken);

            ReplaceMemory(
                memory);

            if (IsSelectedMemory(
                memoryId))
            {
                SelectedMemory =
                    memory;
            }

            StatusMessage =
                "Memory saved.";
        }
        catch (OperationCanceledException)
        {
            HandleCancellation();
        }
        catch (Exception exception)
        {
            HandleFailure(
                exception,
                "Memory edit failed.");
        }
        finally
        {
            EndOperation();
        }
    }

    public async Task DeleteAsync(
        CancellationToken cancellationToken = default)
    {
        if (IsBusy ||
            !EnsureConnected() ||
            SelectedMemory is null)
        {
            return;
        }

        string memoryId =
            SelectedMemory.MemoryId;

        BeginOperation(
            "Deleting Memory...");

        try
        {
            await _memoryClientService.DeleteAsync(
                memoryId,
                cancellationToken);

            RemoveMemory(
                memoryId);

            if (IsSelectedMemory(
                memoryId))
            {
                SelectedMemory = null;
            }

            HasLoaded = true;

            NotifyMemoryCollectionChanged();

            StatusMessage =
                "Memory deleted.";
        }
        catch (OperationCanceledException)
        {
            HandleCancellation();
        }
        catch (Exception exception)
        {
            HandleFailure(
                exception,
                "Memory deletion failed.");
        }
        finally
        {
            EndOperation();
        }
    }

    public async Task LoadHistoryAsync(
        CancellationToken cancellationToken = default)
    {
        if (IsBusy ||
            !EnsureConnected() ||
            SelectedMemory is null)
        {
            return;
        }

        string memoryId =
            SelectedMemory.MemoryId;

        BeginOperation(
            "Loading Memory history...");

        try
        {
            IReadOnlyList<MemoryRevisionPayload> revisions =
                await _memoryClientService.GetHistoryAsync(
                    memoryId,
                    cancellationToken);

            if (!IsSelectedMemory(
                memoryId))
            {
                StatusMessage =
                    "Memory selection changed.";

                return;
            }

            History.Clear();

            foreach (
                MemoryRevisionPayload revision
                in revisions)
            {
                History.Add(
                    revision);
            }

            IsHistoryVisible = true;

            StatusMessage =
                $"Loaded {History.Count} revisions.";
        }
        catch (OperationCanceledException)
        {
            HandleCancellation();
        }
        catch (Exception exception)
        {
            HandleFailure(
                exception,
                "Memory history failed.");
        }
        finally
        {
            EndOperation();
        }
    }

    public void HideHistory()
    {
        IsHistoryVisible = false;
    }

    private bool EnsureConnected()
    {
        RefreshConnectionState();

        if (IsConnected)
        {
            return true;
        }

        ErrorMessage =
            "Agent Core is not connected.";

        StatusMessage =
            "Memory unavailable.";

        return false;
    }

    private void BeginOperation(
        string statusMessage,
        bool isLoading = false)
    {
        ErrorMessage = null;

        IsBusy = true;

        if (isLoading)
        {
            IsLoading = true;
        }

        StatusMessage =
            statusMessage;
    }

    private void EndOperation(
        bool isLoading = false)
    {
        if (isLoading)
        {
            IsLoading = false;
        }

        IsBusy = false;

        RefreshConnectionState();
    }

    private void ReplaceMemory(
        MemoryEntryPayload memory)
    {
        for (int index = 0;
             index < Memories.Count;
             index++)
        {
            if (!string.Equals(
                Memories[index].MemoryId,
                memory.MemoryId,
                StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            Memories[index] =
                memory;

            NotifyMemoryCollectionChanged();

            return;
        }
    }

    private void RemoveMemory(
        string memoryId)
    {
        MemoryEntryPayload? memory =
            Memories.FirstOrDefault(
                item => string.Equals(
                    item.MemoryId,
                    memoryId,
                    StringComparison.OrdinalIgnoreCase));

        if (memory is null)
        {
            return;
        }

        Memories.Remove(
            memory);
    }

    private void ClearHistory()
    {
        History.Clear();

        IsHistoryVisible = false;
    }

    private void HandleCancellation()
    {
        ErrorMessage = null;

        StatusMessage =
            "Memory operation canceled.";
    }

    private void HandleFailure(
        Exception exception,
        string statusMessage)
    {
        ErrorMessage =
            exception is MemoryClientException memoryError
                ? memoryError.Message
                : "Memory operation failed.";

        StatusMessage =
            statusMessage;
    }

    private void NotifyMemoryCollectionChanged()
    {
        OnPropertyChanged(nameof(HasMemories));
        OnPropertyChanged(nameof(IsEmpty));
    }

    private void NotifyOperationStateChanged()
    {
        OnPropertyChanged(nameof(CanOperate));
        OnPropertyChanged(nameof(CanSave));
        OnPropertyChanged(nameof(CanDelete));
        OnPropertyChanged(nameof(CanLoadHistory));
    }

    private void OnPropertyChanged(
        [CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(
            this,
            new PropertyChangedEventArgs(
                propertyName));
    }

    private bool IsSelectedMemory(
        string memoryId)
    {
        return string.Equals(
            SelectedMemory?.MemoryId,
            memoryId,
            StringComparison.OrdinalIgnoreCase);
    }
}
