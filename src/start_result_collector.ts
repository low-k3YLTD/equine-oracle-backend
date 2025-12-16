import { resultCollector } from "./agents/resultCollector";

async function main() {
    console.log("Starting Result Collector Test...");
    
    // Register a prediction that the collector can match
    resultCollector.registerPrediction("rc_103", "Tulloch", "Randwick", 0.8, "2.0-oracle-engine");
    resultCollector.registerPrediction("rc_103", "Might and Power", "Randwick", 0.2, "2.0-oracle-engine");

    await resultCollector.start();
    
    // Stop after a single cycle for testing purposes
    setTimeout(() => {
        resultCollector.stop();
        console.log("Result Collector Test Finished.");
        console.log("Collector Metrics:", resultCollector.getMetrics());
    }, 5000);
}

main().catch(console.error);
