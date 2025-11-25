/**
 * Iframe Multiplier Extractor
 * Extracts the exact multiplier value displayed in the Aviator game iframe
 * Supports multiple extraction methods:
 * 1. OCR-based extraction from canvas/DOM
 * 2. Regex pattern matching from visible text
 * 3. API calls to game backend
 * 4. PostMessage communication with iframe
 */

export interface MultiplierExtractionResult {
  multiplier: number | null;
  method: "ocr" | "regex" | "api" | "postmessage" | "state" | "xpath" | "failed";
  confidence: number; // 0-1
  rawValue?: string;
  timestamp: string;
  error?: string;
}

/**
 * Extract multiplier from iframe using PostMessage
 * This is the most reliable method if the iframe supports it
 */
export async function extractMultiplierViaPostMessage(
  iframeRef: React.RefObject<HTMLIFrameElement>
): Promise<MultiplierExtractionResult> {
  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      resolve({
        multiplier: null,
        method: "postmessage",
        confidence: 0,
        timestamp: new Date().toISOString(),
        error: "PostMessage timeout - iframe may not support messaging",
      });
    }, 2000);

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = event.data;
        if (data.type === "MULTIPLIER_UPDATE" && data.multiplier) {
          clearTimeout(timeout);
          window.removeEventListener("message", handleMessage);

          resolve({
            multiplier: parseFloat(data.multiplier),
            method: "postmessage",
            confidence: data.confidence || 0.95,
            rawValue: String(data.multiplier),
            timestamp: new Date().toISOString(),
          });
        }
      } catch (err) {
        // Ignore message parsing errors
      }
    };

    window.addEventListener("message", handleMessage);

    // Send request to iframe
    try {
      iframeRef.current?.contentWindow?.postMessage(
        { type: "GET_MULTIPLIER" },
        "*"
      );
    } catch (err) {
      clearTimeout(timeout);
      resolve({
        multiplier: null,
        method: "postmessage",
        confidence: 0,
        timestamp: new Date().toISOString(),
        error: String(err),
      });
    }
  });
}

/**
 * Extract multiplier from iframe using OCR
 * Requires Tesseract.js or similar OCR library
 * This method captures the current state of the iframe canvas
 */
export async function extractMultiplierViaOCR(
  iframeRef: React.RefObject<HTMLIFrameElement>
): Promise<MultiplierExtractionResult> {
  try {
    const iframe = iframeRef.current;
    if (!iframe || !iframe.contentDocument) {
      return {
        multiplier: null,
        method: "ocr",
        confidence: 0,
        timestamp: new Date().toISOString(),
        error: "Cannot access iframe DOM",
      };
    }

    // Try to find canvas element in iframe
    const canvas = iframe.contentDocument.querySelector("canvas");
    if (!canvas) {
      return {
        multiplier: null,
        method: "ocr",
        confidence: 0,
        timestamp: new Date().toISOString(),
        error: "No canvas found in iframe",
      };
    }

    // For now, we'll use regex extraction instead of full OCR
    // Full OCR would require Tesseract.js library
    return await extractMultiplierViaRegex(iframeRef);
  } catch (err) {
    return {
      multiplier: null,
      method: "ocr",
      confidence: 0,
      timestamp: new Date().toISOString(),
      error: String(err),
    };
  }
}

/**
 * Extract multiplier from iframe using XPath
 * Targets the specific element containing the multiplier value
 * XPath: //*[@id="root"]/div[1]/div[3]/div[2]/div[2]
 */
export async function extractMultiplierViaXPath(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  xpath: string = '//*[@id="root"]/div[1]/div[3]/div[2]/div[2]'
): Promise<MultiplierExtractionResult> {
  try {
    const iframe = iframeRef.current;
    if (!iframe || !iframe.contentDocument) {
      return {
        multiplier: null,
        method: "regex",
        confidence: 0,
        timestamp: new Date().toISOString(),
        error: "Cannot access iframe DOM",
      };
    }

    // Use XPathResult to evaluate the XPath expression
    const result = iframe.contentDocument.evaluate(
      xpath,
      iframe.contentDocument,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null
    );

    const element = result.singleNodeValue as HTMLElement;
    if (!element) {
      return {
        multiplier: null,
        method: "regex",
        confidence: 0,
        timestamp: new Date().toISOString(),
        error: `Element not found at XPath: ${xpath}`,
      };
    }

    // Extract text content from the element
    const text = element.innerText?.trim() || element.textContent?.trim() || "";

    // Parse multiplier from text (handle formats like "1.23", "1.23x", "1.23×")
    const multiplierMatch = text.match(/(\d+\.?\d*)\s*[x×]?/);
    if (multiplierMatch) {
      const multiplier = parseFloat(multiplierMatch[1]);
      if (multiplier > 0 && multiplier < 10000) {
        return {
          multiplier,
          method: "regex",
          confidence: 0.95,
          rawValue: text,
          timestamp: new Date().toISOString(),
        };
      }
    }

    return {
      multiplier: null,
      method: "regex",
      confidence: 0,
      timestamp: new Date().toISOString(),
      error: `Could not parse multiplier from element text: "${text}"`,
    };
  } catch (err) {
    return {
      multiplier: null,
      method: "regex",
      confidence: 0,
      timestamp: new Date().toISOString(),
      error: String(err),
    };
  }
}

/**
 * Extract multiplier from iframe using regex pattern matching
 * Searches for multiplier patterns in iframe content
 */
export async function extractMultiplierViaRegex(
  iframeRef: React.RefObject<HTMLIFrameElement>
): Promise<MultiplierExtractionResult> {
  try {
    const iframe = iframeRef.current;
    if (!iframe || !iframe.contentDocument) {
      return {
        multiplier: null,
        method: "regex",
        confidence: 0,
        timestamp: new Date().toISOString(),
        error: "Cannot access iframe DOM",
      };
    }

    const iframeContent = iframe.contentDocument.documentElement.innerText || "";

    // Common multiplier patterns in Aviator game
    const patterns = [
      /(\d+\.\d{2})x/gi, // Format: 1.23x
      /multiplier[:\s]+(\d+\.\d{2})/gi, // Label format
      /(\d+\.\d{2})\s*×/gi, // Using × symbol
      /crash[:\s]*(\d+\.\d{2})/gi, // Crash multiplier
    ];

    for (const pattern of patterns) {
      const matches = iframeContent.matchAll(pattern);
      for (const match of matches) {
        const multiplier = parseFloat(match[1]);
        if (multiplier > 1 && multiplier < 1000) {
          return {
            multiplier,
            method: "regex",
            confidence: 0.85,
            rawValue: match[0],
            timestamp: new Date().toISOString(),
          };
        }
      }
    }

    return {
      multiplier: null,
      method: "regex",
      confidence: 0,
      timestamp: new Date().toISOString(),
      error: "No multiplier pattern found",
    };
  } catch (err) {
    return {
      multiplier: null,
      method: "regex",
      confidence: 0,
      timestamp: new Date().toISOString(),
      error: String(err),
    };
  }
}

/**
 * Extract multiplier via iframe API call
 * Some game backends provide API endpoints for current game state
 * Note: This may fail due to CORS in local development environments
 */
export async function extractMultiplierViaAPI(
  sessionId?: string,
  skipIfCrossOrigin: boolean = true
): Promise<MultiplierExtractionResult> {
  try {
    // Skip API calls in development/demo environments where CORS errors are common
    if (skipIfCrossOrigin && typeof window !== "undefined") {
      const isDemoEnv =
        window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1" ||
        window.location.hostname.includes("demo");

      if (isDemoEnv) {
        return {
          multiplier: null,
          method: "api",
          confidence: 0,
          timestamp: new Date().toISOString(),
          error: "API calls skipped in demo environment (use regex or postmessage instead)",
        };
      }
    }

    // This would depend on the specific game backend
    // For Aviator demo, we might call an API like:
    // https://demo.aviatrix.bet/api/current-multiplier

    const response = await fetch("https://demo.aviatrix.bet/api/game/state", {
      headers: {
        sessionId: sessionId || "",
      },
    });

    if (!response.ok) {
      return {
        multiplier: null,
        method: "api",
        confidence: 0,
        timestamp: new Date().toISOString(),
        error: `API returned ${response.status}`,
      };
    }

    const data = await response.json();
    const multiplier = parseFloat(data.currentMultiplier || data.multiplier || 0);

    if (multiplier > 1 && multiplier < 1000) {
      return {
        multiplier,
        method: "api",
        confidence: 0.99,
        rawValue: String(data.currentMultiplier || data.multiplier),
        timestamp: new Date().toISOString(),
      };
    }

    return {
      multiplier: null,
      method: "api",
      confidence: 0,
      timestamp: new Date().toISOString(),
      error: "Invalid multiplier from API",
    };
  } catch (err) {
    return {
      multiplier: null,
      method: "api",
      confidence: 0,
      timestamp: new Date().toISOString(),
      error: String(err),
    };
  }
}

/**
 * Extract screenshot from iframe for manual inspection
 * Returns base64-encoded image of current iframe state
 */
export async function captureIframeScreenshot(
  iframeRef: React.RefObject<HTMLIFrameElement>
): Promise<string | null> {
  try {
    const iframe = iframeRef.current;
    if (!iframe) return null;

    // Use html2canvas or similar library to capture iframe
    // For now, return null as it requires external library
    // Implementation would look like:
    // const canvas = await html2canvas(iframe.contentDocument.body);
    // return canvas.toDataURL('image/png');

    return null;
  } catch (err) {
    console.error("Screenshot capture failed:", err);
    return null;
  }
}

/**
 * Main extraction function - tries multiple methods
 * Returns the most confident result
 * Priority: XPath > PostMessage > Regex > API
 */
export async function extractMultiplier(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  method: "auto" | "postmessage" | "ocr" | "regex" | "api" | "xpath" = "auto",
  customXPath?: string
): Promise<MultiplierExtractionResult> {
  const results: MultiplierExtractionResult[] = [];

  // Try XPath first (highest priority for direct element access)
  if (method === "auto" || method === "xpath") {
    const result = await extractMultiplierViaXPath(iframeRef, customXPath);
    if (result.multiplier !== null && result.confidence > 0.8) {
      return result;
    }
    results.push(result);
  }

  if (method === "auto" || method === "postmessage") {
    const result = await extractMultiplierViaPostMessage(iframeRef);
    if (result.multiplier !== null && result.confidence > 0.8) {
      return result;
    }
    results.push(result);
  }

  if (method === "auto" || method === "regex") {
    const result = await extractMultiplierViaRegex(iframeRef);
    if (result.multiplier !== null && result.confidence > 0.8) {
      return result;
    }
    results.push(result);
  }

  if (method === "auto" || method === "api") {
    const result = await extractMultiplierViaAPI();
    if (result.multiplier !== null && result.confidence > 0.8) {
      return result;
    }
    results.push(result);
  }

  // Return best result, or failure if none worked
  return (
    results.find((r) => r.multiplier !== null) || {
      multiplier: null,
      method: "failed",
      confidence: 0,
      timestamp: new Date().toISOString(),
      error: "All extraction methods failed",
    }
  );
}

/**
 * Continuous extraction - extract multiplier at regular intervals
 * Useful for tracking multiplier changes in real-time
 */
export function startContinuousExtraction(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  onUpdate: (result: MultiplierExtractionResult) => void,
  intervalMs: number = 500
): () => void {
  let lastMultiplier: number | null = null;

  const interval = setInterval(async () => {
    const result = await extractMultiplier(iframeRef, "auto");

    // Only callback if multiplier changed
    if (result.multiplier !== lastMultiplier) {
      lastMultiplier = result.multiplier;
      onUpdate(result);
    }
  }, intervalMs);

  // Return cleanup function
  return () => clearInterval(interval);
}
