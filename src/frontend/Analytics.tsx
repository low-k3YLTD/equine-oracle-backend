import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { trpc } from "@/lib/trpc";
import { Loader2, Filter, TrendingUp } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function Analytics() {
  const [filterTrack, setFilterTrack] = useState("");
  const [filterStartDate, setFilterStartDate] = useState("");
  const [filterEndDate, setFilterEndDate] = useState("");

  const { data: predictions, isLoading: predictionsLoading } = trpc.prediction.history.useQuery();
  const { data: accuracy } = trpc.prediction.accuracy.useQuery();

  // Filter predictions based on criteria
  const filteredPredictions = useMemo(() => {
    if (!predictions) return [];

    return predictions.filter((pred: any) => {
      const predDate = new Date(pred.createdAt);
      const startDate = filterStartDate ? new Date(filterStartDate) : null;
      const endDate = filterEndDate ? new Date(filterEndDate) : null;

      if (startDate && predDate < startDate) return false;
      if (endDate && predDate > endDate) return false;

      return true;
    });
  }, [predictions, filterStartDate, filterEndDate]);

  // Calculate trend data
  const trendData = useMemo(() => {
    if (!filteredPredictions || filteredPredictions.length === 0) {
      return { byConfidence: {}, byRank: {}, byDate: {} };
    }

    const byConfidence: { [key: string]: number } = {};
    const byRank: { [key: string]: number } = { "1": 0, "2": 0, "3": 0, "4": 0 };
    const byDate: { [key: string]: { correct: number; total: number } } = {};

    filteredPredictions.forEach((pred: any) => {
      // Confidence distribution
      const confScore = parseFloat(pred.confidenceScore);
      const confBucket = Math.floor(confScore / 10) * 10;
      byConfidence[`${confBucket}-${confBucket + 10}%`] =
        (byConfidence[`${confBucket}-${confBucket + 10}%`] || 0) + 1;

      // Rank distribution
      byRank[pred.predictedRank] = (byRank[pred.predictedRank] || 0) + 1;

      // Date-based accuracy
      const dateKey = new Date(pred.createdAt).toLocaleDateString();
      if (!byDate[dateKey]) {
        byDate[dateKey] = { correct: 0, total: 0 };
      }
      byDate[dateKey].total += 1;
      if (pred.isCorrect === 1) {
        byDate[dateKey].correct += 1;
      }
    });

    return { byConfidence, byRank, byDate };
  }, [filteredPredictions]);

  const verifiedCount = filteredPredictions.filter((p: any) => p.actualRank !== null).length;
  const correctCount = filteredPredictions.filter((p: any) => p.isCorrect === 1).length;
  const filteredAccuracy =
    verifiedCount > 0 ? Math.round((correctCount / verifiedCount) * 100 * 100) / 100 : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Advanced Analytics</h1>
          <p className="text-gray-300">Filter and analyze your prediction performance</p>
        </div>

        {/* Filters */}
        <Card className="bg-gray-900/50 border-gray-700/50 mb-8">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Filter className="w-5 h-5" />
              Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="filter-track" className="text-gray-300">
                  Track
                </Label>
                <Input
                  id="filter-track"
                  value={filterTrack}
                  onChange={(e) => setFilterTrack(e.target.value)}
                  placeholder="Filter by track"
                  className="bg-gray-800 border-gray-600 text-white"
                />
              </div>
              <div>
                <Label htmlFor="filter-start" className="text-gray-300">
                  Start Date
                </Label>
                <Input
                  id="filter-start"
                  type="date"
                  value={filterStartDate}
                  onChange={(e) => setFilterStartDate(e.target.value)}
                  className="bg-gray-800 border-gray-600 text-white"
                />
              </div>
              <div>
                <Label htmlFor="filter-end" className="text-gray-300">
                  End Date
                </Label>
                <Input
                  id="filter-end"
                  type="date"
                  value={filterEndDate}
                  onChange={(e) => setFilterEndDate(e.target.value)}
                  className="bg-gray-800 border-gray-600 text-white"
                />
              </div>
            </div>
            {(filterTrack || filterStartDate || filterEndDate) && (
              <Button
                onClick={() => {
                  setFilterTrack("");
                  setFilterStartDate("");
                  setFilterEndDate("");
                }}
                variant="outline"
                className="mt-4 border-gray-600"
              >
                Clear Filters
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-purple-900/50 border-purple-500/30">
            <CardContent className="pt-6">
              <p className="text-gray-300 text-sm mb-2">Total Predictions</p>
              <p className="text-3xl font-bold text-white">{filteredPredictions.length}</p>
            </CardContent>
          </Card>

          <Card className="bg-blue-900/50 border-blue-500/30">
            <CardContent className="pt-6">
              <p className="text-gray-300 text-sm mb-2">Verified</p>
              <p className="text-3xl font-bold text-blue-400">{verifiedCount}</p>
            </CardContent>
          </Card>

          <Card className="bg-green-900/50 border-green-500/30">
            <CardContent className="pt-6">
              <p className="text-gray-300 text-sm mb-2">Correct</p>
              <p className="text-3xl font-bold text-green-400">{correctCount}</p>
            </CardContent>
          </Card>

          <Card className="bg-yellow-900/50 border-yellow-500/30">
            <CardContent className="pt-6">
              <p className="text-gray-300 text-sm mb-2">Accuracy</p>
              <p className="text-3xl font-bold text-yellow-400">{filteredAccuracy}%</p>
            </CardContent>
          </Card>
        </div>

        {/* Trend Analysis */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Confidence Distribution */}
          <Card className="bg-gray-900/50 border-gray-700/50">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Confidence Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              {Object.entries(trendData.byConfidence).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(trendData.byConfidence)
                    .sort(([a], [b]) => {
                      const aNum = parseInt(a.split("-")[0]);
                      const bNum = parseInt(b.split("-")[0]);
                      return aNum - bNum;
                    })
                    .map(([range, count]) => (
                      <div key={range}>
                        <div className="flex justify-between mb-1">
                          <span className="text-gray-300 text-sm">{range}</span>
                          <span className="text-gray-300 text-sm font-semibold">{count}</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                            style={{
                              width: `${(count / Math.max(...Object.values(trendData.byConfidence))) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <Alert>
                  <AlertDescription>No data available</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Rank Distribution */}
          <Card className="bg-gray-900/50 border-gray-700/50">
            <CardHeader>
              <CardTitle className="text-white">Predicted Rank Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              {Object.entries(trendData.byRank).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(trendData.byRank).map(([rank, count]) => (
                    <div key={rank}>
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-300 text-sm">Rank {rank}</span>
                        <span className="text-gray-300 text-sm font-semibold">{count}</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full"
                          style={{
                            width: `${(count / Math.max(...Object.values(trendData.byRank))) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <Alert>
                  <AlertDescription>No data available</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Daily Accuracy Trend */}
        {Object.keys(trendData.byDate).length > 0 && (
          <Card className="bg-gray-900/50 border-gray-700/50 mt-8">
            <CardHeader>
              <CardTitle className="text-white">Daily Accuracy Trend</CardTitle>
              <CardDescription>Accuracy percentage by date</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(trendData.byDate)
                  .sort(([dateA], [dateB]) => new Date(dateA).getTime() - new Date(dateB).getTime())
                  .slice(-7) // Show last 7 days
                  .map(([date, { correct, total }]) => {
                    const dayAccuracy = total > 0 ? Math.round((correct / total) * 100) : 0;
                    return (
                      <div key={date}>
                        <div className="flex justify-between mb-1">
                          <span className="text-gray-300 text-sm">{date}</span>
                          <span className="text-gray-300 text-sm font-semibold">
                            {correct}/{total} ({dayAccuracy}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full"
                            style={{ width: `${dayAccuracy}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
