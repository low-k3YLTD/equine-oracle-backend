import { continuousPredictionAgent } from "./agents/continuousPredictionAgent";

async function main() {
    console.log("Starting Continuous Prediction Agent Test...");
    await continuousPredictionAgent.start();
    
    // Stop after a single cycle for testing purposes
    setTimeout(() => {
        continuousPredictionAgent.stop();
        console.log("Continuous Prediction Agent Test Finished.");
    }, 5000);
}

main().catch(console.error);
