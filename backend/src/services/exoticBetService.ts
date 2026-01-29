import { spawn } from 'child_process';
import * as path from 'path';

const EXOTIC_API_PATH = path.join(__dirname, 'exotic_bet_optimizer', 'exotic_bet_api.py');

export interface HorseInput {
    id: number;
    name: string;
    win_probability: number;
    odds: number;
    jockey?: string;
    trainer?: string;
    form_rating?: number;
    speed_rating?: number;
    class_rating?: number;
}

export interface OptimizationOptions {
    max_exacta?: number;
    max_trifecta?: number;
    max_superfecta?: number;
    min_ev_threshold?: number;
}

export interface OptimizationRequest {
    race_id: string;
    horses: HorseInput[];
    options?: OptimizationOptions;
}

/**
 * Calls the Python Exotic Bet Optimizer script with input data and returns the results.
 * This service currently interacts with the Python script via a child process for simplicity,
 * but it could be modified to call a running Flask service if needed.
 */
export function optimizeExoticBets(request: OptimizationRequest): Promise<any> {
    return new Promise((resolve, reject) => {
        // We use a temporary wrapper or call the Flask app's logic directly if possible.
        // For now, we'll spawn the python process and pass the JSON.
        // Note: exotic_bet_api.py is designed as a Flask app, so we might need a 
        // bridge or to call it via HTTP if it's running.
        // However, for a quick win, we can call the optimizer logic directly.
        
        const OPTIMIZER_BRIDGE_PATH = path.join(__dirname, 'exotic_bet_optimizer', 'exotic_bet_optimizer.py');
        const pythonProcess = spawn('python3', [OPTIMIZER_BRIDGE_PATH]);
        
        let output = '';
        let error = '';

        // The optimizer script expects horses as input if we modify its main.
        // For now, let's assume we've modified it to read from stdin like ml_api_service.py
        pythonProcess.stdin.write(JSON.stringify(request.horses));
        pythonProcess.stdin.end();

        pythonProcess.stdout.on('data', (data) => {
            output += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            error += data.toString();
        });

        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(`Exotic optimizer failed: ${error}`));
                return;
            }

            try {
                // The script currently prints a lot of info, we need to extract the JSON
                const jsonMatch = output.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                    resolve(JSON.parse(jsonMatch[0]));
                } else {
                    reject(new Error("No JSON output found from optimizer"));
                }
            } catch (e) {
                reject(new Error(`Failed to parse optimizer output: ${e}`));
            }
        });
    });
}
