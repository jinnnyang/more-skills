import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import * as dotenv from 'dotenv';
import { ChatCompletionMessageParam } from 'openai/resources/chat/completions';

// Load .env from the root of the skill directory if it exists
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const skillDir = path.resolve(__dirname, '..');
dotenv.config({ path: path.join(skillDir, '.env') });

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENAI_BASE_URL = process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1';
const OPENAI_MODEL_NAME = process.env.OPENAI_MODEL_NAME || 'gpt-4o';

if (!OPENAI_API_KEY) {
  console.error('\n[AGENT GUIDANCE - ERROR]');
  console.error('The OPENAI_API_KEY environment variable is not set. Please ask the user to provide their OpenAI API key, or create a .env file in the skill directory containing it.');
  console.error('Do not attempt to guess or proceed without it.');
  process.exit(1);
}

interface ImageDesc {
  alt: string;
  title: string;
}

/**
 * Helper to fetch a remote image and return its mime type and base64 string
 */
async function fetchRemoteImage(url: string): Promise<{ mime: string; base64: string }> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch image from URL: ${response.statusText}`);
  }
  const mime = response.headers.get('content-type') || 'image/jpeg';
  const arrayBuffer = await response.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);
  return { mime, base64: buffer.toString('base64') };
}

/**
 * Helper to read a local image and return its mime type and base64 string
 */
async function readLocalImage(filePath: string): Promise<{ mime: string; base64: string }> {
  const ext = path.extname(filePath).toLowerCase();
  let mime = 'image/jpeg';
  if (ext === '.png') mime = 'image/png';
  else if (ext === '.gif') mime = 'image/gif';
  else if (ext === '.webp') mime = 'image/webp';
  else if (ext === '.svg') mime = 'image/svg+xml';

  const buffer = await fs.readFile(filePath);
  return { mime, base64: buffer.toString('base64') };
}

/**
 * Base request logic for OpenAI Chat Completions
 */
async function makeChatRequest(messages: ChatCompletionMessageParam[], systemPrompt: string, responseFormat: 'text' | 'json_object' = 'text'): Promise<string> {
  const body = {
    model: OPENAI_MODEL_NAME,
    messages: [
      { role: 'system', content: systemPrompt } as ChatCompletionMessageParam,
      ...messages
    ],
    response_format: { type: responseFormat }
  };

  const response = await fetch(`${OPENAI_BASE_URL.replace(/\/$/, '')}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${OPENAI_API_KEY}`
    },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`OpenAI API Error (${response.status}): ${errText}`);
  }

  const json = await response.json();
  return json.choices[0].message.content;
}

export interface GlobalMetadata {
  language: string;
  title: string;
  description: string;
  keywords: string;
  author: string;
}

/**
 * Extract global metadata from markdown text
 */
export async function extractGlobalMetadata(markdownText: string, codeTitle?: string): Promise<GlobalMetadata> {
  const systemPrompt = "You are an expert document analyzer. Read the provided markdown text and extract metadata. Return strictly as a JSON object: {\"language\": \"primary language name, e.g. Chinese\", \"title\": \"document title\", \"description\": \"concise summary written in the detected primary language\", \"keywords\": \"comma separated keywords written in the detected primary language\", \"author\": \"author name if found, else empty string\"}.";
  
  // Truncate to first 4000 characters to save tokens, usually enough for metadata
  const contentToAnalyze = markdownText.slice(0, 4000);
  
  const messages: ChatCompletionMessageParam[] = [
    {
      role: 'user',
      content: `Here is the start of the document:\n\n${contentToAnalyze}\n\n${codeTitle ? `(Note: The document title is known to be: ${codeTitle})\n` : ''}`
    }
  ];

  try {
    const resultText = await makeChatRequest(messages, systemPrompt, 'json_object');
    return JSON.parse(resultText) as GlobalMetadata;
  } catch (error) {
    console.error(`Error extracting global metadata:`, error);
    return { language: 'English', title: '', description: '', keywords: '', author: '' };
  }
}

/**
 * Analyze an image and return suitable alt and title texts
 */
export async function analyzeImage(imageUrlOrPath: string, globalLanguage: string, contextText?: string): Promise<ImageDesc> {
  let mime: string;
  let base64: string;

  try {
    if (imageUrlOrPath.startsWith('http://') || imageUrlOrPath.startsWith('https://')) {
      const res = await fetchRemoteImage(imageUrlOrPath);
      mime = res.mime;
      base64 = res.base64;
    } else {
      const res = await readLocalImage(imageUrlOrPath);
      mime = res.mime;
      base64 = res.base64;
    }
  } catch (error) {
    console.warn(`Warning: Could not process image ${imageUrlOrPath}. Reason: ${error}`);
    // Return empty strings so we don't crash the whole pipeline for one bad image
    return { alt: '', title: '' };
  }

  const systemPrompt = `You are an expert accessibility consultant and data analyst. You describe images accurately and concisely for visually impaired readers.
CRITICAL RULES:
1. Your ENTIRE output (alt and title) MUST be written in this EXACT language: ${globalLanguage}. DO NOT USE ANY OTHER LANGUAGE!
2. If the image contains quantitative indicators, charts, or metrics, you MUST capture the specific numbers, trends, and data points accurately.
3. Return the response strictly as a JSON object: {"alt": "...", "title": "..."}`;
  
  const textContent = contextText ? 
    `Here is the textual context around the image in the document:\n"""\n${contextText}\n"""\n\nAnalyze this image and provide a highly descriptive alt text (what the image contains physically, including any specific quantitative metrics or data points shown) and a concise title (a short name or caption). REMEMBER TO OUTPUT STRICTLY IN: ${globalLanguage}! Return the response strictly as a JSON object: {"alt": "...", "title": "..."}` :
    `Analyze this image and provide a highly descriptive alt text (what the image contains physically) and a concise title (a short name or caption). REMEMBER TO OUTPUT STRICTLY IN: ${globalLanguage}! Return the response strictly as a JSON object: {"alt": "...", "title": "..."}`;

  const messages: ChatCompletionMessageParam[] = [
    {
      role: 'user',
      content: [
        {
          type: 'text',
          text: textContent
        },
        {
          type: 'image_url',
          image_url: {
            url: `data:${mime};base64,${base64}`
          }
        }
      ]
    }
  ];

  try {
    const resultText = await makeChatRequest(messages, systemPrompt, 'json_object');
    return JSON.parse(resultText) as ImageDesc;
  } catch (error) {
    console.error(`Error analyzing image via LLM:`, error);
    return { alt: '', title: '' };
  }
}

/**
 * Infer programming language from code block
 */
export async function inferCodeLanguage(code: string): Promise<string> {
  const systemPrompt = "You are a code detection tool. Your only output should be the lowercase name of the programming language (e.g. 'python', 'javascript', 'typescript', 'bash', 'json', 'html', 'css', 'yaml'). If you cannot detect it confidently, output 'text'. Do not wrap in markdown quotes.";
  const messages: ChatCompletionMessageParam[] = [
    {
      role: 'user',
      content: code
    }
  ];

  try {
    const resultText = await makeChatRequest(messages, systemPrompt, 'text');
    return resultText.trim().toLowerCase().replace(/`/g, '');
  } catch (error) {
    console.error(`Error inferring code language via LLM:`, error);
    return '';
  }
}
