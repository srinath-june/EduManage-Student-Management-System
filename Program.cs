// ============================================================================
// EduManage Report Generator (.NET Console Tool)
//
// This is a basic .NET (C#) console application that demonstrates cross-stack
// integration: it calls the Python Flask REST API (backend/app.py) over HTTP,
// deserializes the JSON response, and generates an attendance/department
// report as both a console summary and a CSV file.
//
// It shows fundamental .NET concepts: HttpClient, async/await, LINQ,
// records/classes, JSON serialization, and file I/O.
//
// HOW TO RUN:
//   1. Start the Flask backend first:  python app.py   (listens on :5000)
//   2. cd dotnet-report-tool
//   3. dotnet run
//
// Requires the .NET 8 SDK: https://dotnet.microsoft.com/download
// ============================================================================

using System.Text.Json;
using System.Text.Json.Serialization;

namespace EduManage.ReportGenerator;

// A basic .NET model class matching the JSON returned by the Flask API's
// /api/public/report-data endpoint.
public class Student
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("roll_number")]
    public string RollNumber { get; set; } = string.Empty;

    [JsonPropertyName("department")]
    public string Department { get; set; } = string.Empty;

    [JsonPropertyName("year")]
    public int Year { get; set; }

    [JsonPropertyName("email")]
    public string Email { get; set; } = string.Empty;

    [JsonPropertyName("attendance_percent")]
    public double AttendancePercent { get; set; }
}

internal class Program
{
    // Base URL of the Python Flask backend
    private const string ApiBaseUrl = "http://127.0.0.1:5000";

    private static async Task<int> Main(string[] args)
    {
        Console.WriteLine("=====================================================");
        Console.WriteLine("   EduManage Report Generator  (.NET Console Tool)");
        Console.WriteLine("   Fetching live data from the Python Flask API...");
        Console.WriteLine("=====================================================\n");

        List<Student>? students;

        try
        {
            students = await FetchStudentsAsync();
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine("ERROR: Could not reach the Flask API.");
            Console.WriteLine($"       Make sure 'python app.py' is running on {ApiBaseUrl}.");
            Console.WriteLine($"       Details: {ex.Message}");
            return 1;
        }

        if (students is null || students.Count == 0)
        {
            Console.WriteLine("No student records were returned by the API.");
            return 0;
        }

        PrintConsoleSummary(students);

        string csvPath = Path.Combine(Directory.GetCurrentDirectory(), "attendance_report.csv");
        WriteCsvReport(students, csvPath);
        Console.WriteLine($"\nCSV report written to: {csvPath}");

        return 0;
    }

    // Basic HttpClient usage — calls the Flask REST endpoint and deserializes JSON.
    private static async Task<List<Student>?> FetchStudentsAsync()
    {
        using var client = new HttpClient
        {
            BaseAddress = new Uri(ApiBaseUrl),
            Timeout = TimeSpan.FromSeconds(10),
        };

        // This is the PUBLIC endpoint exposed by the Flask backend specifically
        // so external tools (like this .NET app) can pull report data without auth.
        HttpResponseMessage response = await client.GetAsync("/api/public/report-data");
        response.EnsureSuccessStatusCode();

        string json = await response.Content.ReadAsStringAsync();

        var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        return JsonSerializer.Deserialize<List<Student>>(json, options);
    }

    // Demonstrates LINQ grouping/aggregation — basic .NET data processing.
    private static void PrintConsoleSummary(List<Student> students)
    {
        Console.WriteLine($"Total students: {students.Count}\n");

        var byDept = students
            .GroupBy(s => s.Department)
            .OrderBy(g => g.Key)
            .Select(g => new
            {
                Department = g.Key,
                Count = g.Count(),
                AvgAttendance = Math.Round(g.Average(s => s.AttendancePercent), 2),
            });

        Console.WriteLine("Department Summary:");
        Console.WriteLine("--------------------------------------------");
        Console.WriteLine($"{"Dept",-10}{"Students",-12}{"Avg Attendance",-15}");
        Console.WriteLine("--------------------------------------------");
        foreach (var row in byDept)
        {
            Console.WriteLine($"{row.Department,-10}{row.Count,-12}{row.AvgAttendance + "%",-15}");
        }

        var lowAttendance = students.Where(s => s.AttendancePercent < 80).ToList();
        if (lowAttendance.Count > 0)
        {
            Console.WriteLine("\nStudents below 80% attendance (needs attention):");
            foreach (var s in lowAttendance)
            {
                Console.WriteLine($"  - {s.Name} ({s.RollNumber}, {s.Department}): {s.AttendancePercent}%");
            }
        }
    }

    // Basic file I/O — writes a CSV report to disk.
    private static void WriteCsvReport(List<Student> students, string path)
    {
        using var writer = new StreamWriter(path);
        writer.WriteLine("Id,Name,RollNumber,Department,Year,Email,AttendancePercent");

        foreach (var s in students.OrderBy(s => s.Department).ThenBy(s => s.Name))
        {
            writer.WriteLine($"{s.Id},{s.Name},{s.RollNumber},{s.Department},{s.Year},{s.Email},{s.AttendancePercent}");
        }
    }
}
