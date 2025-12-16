import { spawn } from 'child_process';
import * as path from 'path';

const ML_SCRIPT_PATH = path.join(__dirname, 'ml_api_service.py');

interface PredictionInput {
    [key: string]: any;
}

interface PredictionOutput {
    probability: number;
    confidence: number;
}

/**
 * Calls the Python ML model script with input data and returns the predictions.
 * @param inputData An array of feature objects for each horse.
 * @returns A promise that resolves to an array of prediction results.
 */
export function getMlPredictions(inputData: PredictionInput[]): Promise<PredictionOutput[]> {
    return new Promise((resolve, reject) => {
        const pythonProcess = spawn('python3', [ML_SCRIPT_PATH]);
        let output = '';
        let error = '';

        // Send input data to the Python script's stdin
        pythonProcess.stdin.write(JSON.stringify(inputData));
        pythonProcess.stdin.end();

        // Collect data from stdout
        pythonProcess.stdout.on('data', (data) => {
            output += data.toString();
        });

        // Collect data from stderr
        pythonProcess.stderr.on('data', (data) => {
            error += data.toString();
        });

        // Handle process exit
        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                console.error(`ML script exited with code ${code}`);
                console.error(`ML script stderr: ${error}`);
                return reject(new Error(`ML prediction failed: ${error}`));
            }

            try {
                const predictions = JSON.parse(output);
                resolve(predictions);
            } catch (e) {
                console.error(`Failed to parse ML script output: ${output}`);
                console.error(`ML script stderr: ${error}`);
                reject(new Error(`Failed to parse ML script output: ${e}`));
            }
        });

        // Handle process error (e.g., python not found)
        pythonProcess.on('error', (err) => {
            reject(new Error(`Failed to start ML process: ${err.message}`));
        });
    });
}
