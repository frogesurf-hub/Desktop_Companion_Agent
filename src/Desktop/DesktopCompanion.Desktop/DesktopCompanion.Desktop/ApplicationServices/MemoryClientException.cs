namespace DesktopCompanion.Desktop.ApplicationServices;

public sealed class MemoryClientException : Exception
{
    public MemoryClientException(
        string code,
        string message)
        : base(message)
    {
        Code = code;
    }

    public string Code { get; }
}
