import { BingClient } from './engines/cn.bing.com.js';
const ENGINES = {
    'bing': BingClient,
    'cn.bing.com': BingClient
};
async function main() {
    const args = process.argv.slice(2);
    const queries = [];
    let engineOpt = null;
    let format = 'raw';
    const positionals = [];
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '--query' || arg === '-q') {
            const nextVal = args[i + 1];
            if (nextVal && !nextVal.startsWith('-')) {
                queries.push(nextVal);
                i++;
            }
        }
        else if (arg === '--engine') {
            const nextVal = args[i + 1];
            if (nextVal && !nextVal.startsWith('-')) {
                engineOpt = nextVal;
                i++;
            }
        }
        else if (arg === '--format') {
            const nextVal = args[i + 1];
            if (nextVal && !nextVal.startsWith('-')) {
                format = nextVal.toLowerCase();
                i++;
            }
        }
        else if (arg.startsWith('--query=')) {
            queries.push(arg.substring(8));
        }
        else if (arg.startsWith('-q=')) {
            queries.push(arg.substring(3));
        }
        else if (arg.startsWith('--engine=')) {
            engineOpt = arg.substring(9);
        }
        else if (arg.startsWith('--format=')) {
            format = arg.substring(9).toLowerCase();
        }
        else if (!arg.startsWith('-')) {
            positionals.push(arg);
        }
    }
    // Parse output_type and input_type from positionals
    let output_type = 'pages';
    let input_type = 'texts';
    const cleanPositionals = positionals.filter(p => p.toLowerCase() !== 'by');
    if (cleanPositionals.length >= 1) {
        output_type = cleanPositionals[0].toLowerCase();
    }
    if (cleanPositionals.length >= 2) {
        input_type = cleanPositionals[1].toLowerCase();
    }
    const validOutputs = ['pages', 'images', 'videos', 'papers', 'locations', 'terms'];
    const validInputs = ['texts', 'images'];
    if (!validOutputs.includes(output_type)) {
        console.error(`Error: Invalid output type "${output_type}". Supported: ${validOutputs.join(', ')}`);
        process.exit(1);
    }
    if (!validInputs.includes(input_type)) {
        console.error(`Error: Invalid input type "${input_type}". Supported: ${validInputs.join(', ')}`);
        process.exit(1);
    }
    if (queries.length === 0) {
        console.error('Error: No search queries provided. Use --query or -q to specify what to search.');
        process.exit(1);
    }
    if (!['raw', 'json', 'markdown'].includes(format)) {
        console.error(`Error: Invalid format "${format}". Supported: raw, json, markdown`);
        process.exit(1);
    }
    // Resolve engines to run
    const enginesToRun = [];
    if (engineOpt) {
        const key = engineOpt.toLowerCase();
        const ClientClass = ENGINES[key];
        if (!ClientClass) {
            console.error(`Error: Unknown engine "${engineOpt}". Supported: ${Object.keys(ENGINES).join(', ')}`);
            process.exit(1);
        }
        enginesToRun.push({ name: key, ClientClass });
    }
    else {
        // If omitted, run all unique engine classes
        const uniqueClasses = new Map();
        for (const [key, ClientClass] of Object.entries(ENGINES)) {
            if (!uniqueClasses.has(ClientClass)) {
                uniqueClasses.set(ClientClass, key);
            }
        }
        for (const [ClientClass, name] of uniqueClasses.entries()) {
            enginesToRun.push({ name, ClientClass });
        }
    }
    try {
        if (format === 'raw') {
            // Raw HTML mode
            const rawOutputs = [];
            for (const { name, ClientClass } of enginesToRun) {
                const client = new ClientClass();
                for (const query of queries) {
                    try {
                        const rawHtml = await client.get_raw_html(output_type, input_type, query);
                        if (enginesToRun.length > 1 || queries.length > 1) {
                            rawOutputs.push(`<!-- START ENGINE: ${name} | QUERY: ${query} -->\n${rawHtml}\n<!-- END ENGINE: ${name} -->`);
                        }
                        else {
                            rawOutputs.push(rawHtml);
                        }
                    }
                    catch (err) {
                        console.error(`[Error] Engine "${name}" failed query "${query}": ${err.message}`);
                    }
                }
            }
            console.log(rawOutputs.join('\n\n'));
        }
        else {
            // Structured JSON / Markdown mode
            let aggregatedResults = [];
            for (const { name, ClientClass } of enginesToRun) {
                const client = new ClientClass();
                const methodName = `search_${output_type}_by_${input_type}`;
                if (typeof client[methodName] !== 'function') {
                    console.error(`Error: Engine "${name}" does not support combination "${output_type} by ${input_type}"`);
                    process.exit(1);
                }
                for (const query of queries) {
                    try {
                        const results = await client[methodName](query);
                        aggregatedResults.push(...results);
                    }
                    catch (err) {
                        console.error(`[Error] Engine "${name}" failed query "${query}": ${err.message}`);
                    }
                }
            }
            // De-duplicate aggregated results by URL
            const seenUrls = new Set();
            aggregatedResults = aggregatedResults.filter(item => {
                if (seenUrls.has(item.url)) {
                    return false;
                }
                seenUrls.add(item.url);
                return true;
            });
            if (format === 'json') {
                console.log(JSON.stringify(aggregatedResults, null, 2));
            }
            else if (format === 'markdown') {
                if (aggregatedResults.length === 0) {
                    console.log('No search results found.');
                    return;
                }
                if (output_type === 'images') {
                    // SMIS accessibility description image formatting
                    const mdList = aggregatedResults.map((item, idx) => {
                        return `![${item.alt}](${item.url} "${item.title}")`;
                    });
                    console.log(mdList.join('\n\n'));
                }
                else {
                    // Link format for text/videos/papers/etc.
                    const mdList = aggregatedResults.map((item, idx) => {
                        return `${idx + 1}. [${item.title}](${item.url})\n   *${item.alt}*`;
                    });
                    console.log(mdList.join('\n'));
                }
            }
        }
    }
    catch (err) {
        console.error(`\n[AGENT GUIDANCE - FALLBACK STRATEGY]`);
        console.error(`Execution failed: ${err.message}`);
        process.exit(1);
    }
}
main();
