/**
 * Iframe Communication Methods
 * Multiple strategies for communicating with iframes and extracting game state
 */

export interface CommunicationResult {
  method: string;
  success: boolean;
  data?: any;
  error?: string;
  timestamp: string;
  duration: number; // milliseconds
}

/**
 * 1. DOM MUTATION OBSERVER
 * Watch for DOM changes in real-time
 */
export function setupMutationObserver(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  selector: string,
  onUpdate: (text: string, newValue: string) => void
): () => void {
  const iframe = iframeRef.current;
  if (!iframe?.contentDocument) return () => {};

  const targetElement = iframe.contentDocument.querySelector(selector);
  if (!targetElement) return () => {};

  let previousValue = targetElement.textContent || "";

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      const newValue = targetElement.textContent || "";
      if (newValue !== previousValue) {
        onUpdate(previousValue, newValue);
        previousValue = newValue;
      }
    });
  });

  observer.observe(targetElement, {
    characterData: true,
    subtree: true,
    childList: true,
  });

  return () => observer.disconnect();
}

/**
 * 2. POSTING MESSAGE TO IFRAME
 * Send structured messages to iframe API
 */
export async function sendPostMessage(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  message: any,
  targetOrigin: string = "https://demo.aviatrix.bet",
  timeoutMs: number = 5000
): Promise<CommunicationResult> {
  const startTime = performance.now();

  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      window.removeEventListener("message", handler);
      resolve({
        method: "postMessage",
        success: false,
        error: "Timeout waiting for response",
        timestamp: new Date().toISOString(),
        duration: performance.now() - startTime,
      });
    }, timeoutMs);

    const handler = (event: MessageEvent) => {
      if (event.origin !== targetOrigin) return;

      // If message has requestId, match it
      if (message.requestId && event.data.requestId !== message.requestId) {
        return;
      }

      clearTimeout(timeout);
      window.removeEventListener("message", handler);

      resolve({
        method: "postMessage",
        success: true,
        data: event.data,
        timestamp: new Date().toISOString(),
        duration: performance.now() - startTime,
      });
    };

    window.addEventListener("message", handler);

    try {
      const messageWithId = {
        ...message,
        requestId: `req_${Date.now()}_${Math.random()}`,
      };

      iframeRef.current?.contentWindow?.postMessage(
        messageWithId,
        targetOrigin
      );
    } catch (err) {
      clearTimeout(timeout);
      window.removeEventListener("message", handler);

      resolve({
        method: "postMessage",
        success: false,
        error: String(err),
        timestamp: new Date().toISOString(),
        duration: performance.now() - startTime,
      });
    }
  });
}

/**
 * 3. CLICK SIMULATION
 * Simulate user clicks on iframe elements
 */
export function simulateClick(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  selector: string
): CommunicationResult {
  const startTime = performance.now();

  try {
    const iframe = iframeRef.current;
    const element = iframe?.contentDocument?.querySelector(selector);

    if (!element) {
      return {
        method: "simulateClick",
        success: false,
        error: `Element not found: ${selector}`,
        timestamp: new Date().toISOString(),
        duration: performance.now() - startTime,
      };
    }

    const clickEvent = new MouseEvent("click", {
      bubbles: true,
      cancelable: true,
      view: iframe?.contentWindow,
    });

    element.dispatchEvent(clickEvent);

    return {
      method: "simulateClick",
      success: true,
      data: { element: selector },
      timestamp: new Date().toISOString(),
      duration: performance.now() - startTime,
    };
  } catch (err) {
    return {
      method: "simulateClick",
      success: false,
      error: String(err),
      timestamp: new Date().toISOString(),
      duration: performance.now() - startTime,
    };
  }
}

/**
 * 4. DIRECT WINDOW OBJECT ACCESS
 * Access javascript objects exposed by iframe
 */
export async function accessWindowObject(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  objectPath: string // e.g., "Game.state.multiplier" or "window.gameState"
): Promise<CommunicationResult> {
  const startTime = performance.now();

  try {
    const iframe = iframeRef.current;
    if (!iframe?.contentWindow) {
      throw new Error("Cannot access iframe content window");
    }

    // Navigate path: "Game.state.multiplier" → Game → state → multiplier
    const parts = objectPath.split(".");
    let current: any = iframe.contentWindow;

    for (const part of parts) {
      current = current[part];
      if (current === undefined) {
        throw new Error(`Property not found: ${part}`);
      }
    }

    return {
      method: "windowObject",
      success: true,
      data: current,
      timestamp: new Date().toISOString(),
      duration: performance.now() - startTime,
    };
  } catch (err) {
    return {
      method: "windowObject",
      success: false,
      error: String(err),
      timestamp: new Date().toISOString(),
      duration: performance.now() - startTime,
    };
  }
}

/**
 * 5. CALL IFRAME FUNCTION
 * Call javascript functions exposed by iframe
 */
export async function callIframeFunction(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  functionPath: string, // e.g., "Game.getMultiplier"
  args: any[] = []
): Promise<CommunicationResult> {
  const startTime = performance.now();

  try {
    const iframe = iframeRef.current;
    if (!iframe?.contentWindow) {
      throw new Error("Cannot access iframe content window");
    }

    const parts = functionPath.split(".");
    const functionName = parts.pop();
    const obj = parts.reduce((acc, part) => acc[part], iframe.contentWindow as any);

    if (typeof obj[functionName] !== "function") {
      throw new Error(`Function not found or not callable: ${functionPath}`);
    }

    const result = await obj[functionName](...args);

    return {
      method: "callFunction",
      success: true,
      data: result,
      timestamp: new Date().toISOString(),
      duration: performance.now() - startTime,
    };
  } catch (err) {
    return {
      method: "callFunction",
      success: false,
      error: String(err),
      timestamp: new Date().toISOString(),
      duration: performance.now() - startTime,
    };
  }
}

/**
 * 6. REGEX TEXT SEARCH
 * Search for patterns in iframe text content
 */
export function searchIframeText(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  pattern: RegExp | string
): CommunicationResult {
  const startTime = performance.now();

  try {
    const iframe = iframeRef.current;
    const text = iframe?.contentDocument?.documentElement.innerText || "";
    const regex = typeof pattern === "string" ? new RegExp(pattern, "g") : pattern;
    const matches = text.match(regex);

    if (!matches) {
      return {
        method: "regexSearch",
        success: false,
        error: "No matches found",
        timestamp: new Date().toISOString(),
        duration: performance.now() - startTime,
      };
    }

    return {
      method: "regexSearch",
      success: true,
      data: matches,
      timestamp: new Date().toISOString(),
      duration: performance.now() - startTime,
    };
  } catch (err) {
    return {
      method: "regexSearch",
      success: false,
      error: String(err),
      timestamp: new Date().toISOString(),
      duration: performance.now() - startTime,
    };
  }
}

/**
 * 7. CONSOLE INTERCEPTION
 * Intercept iframe console logs to extract data
 */
export function interceptConsole(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  logFilter: (message: string) => boolean = () => true
): () => void {
  const iframe = iframeRef.current;
  if (!iframe?.contentWindow) return () => {};

  const iframeConsole = iframe.contentWindow.console;
  const originalLog = iframeConsole.log;
  const logs: any[] = [];

  iframeConsole.log = function (...args) {
    const message = args.join(" ");
    if (logFilter(message)) {
      logs.push({
        timestamp: new Date().toISOString(),
        message,
        args,
      });
    }
    originalLog.apply(iframeConsole, args);
  };

  return () => {
    iframeConsole.log = originalLog;
  };
}

/**
 * 8. STORAGE WATCHER
 * Monitor localStorage/sessionStorage changes
 */
export function watchStorage(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  onStorageChange: (key: string, newValue: string) => void
): () => void {
  const iframe = iframeRef.current;
  if (!iframe?.contentWindow) return () => {};

  const handleStorageChange = (event: StorageEvent) => {
    if (event.key) {
      onStorageChange(event.key, event.newValue || "");
    }
  };

  iframe.contentWindow.addEventListener("storage", handleStorageChange);

  return () => {
    iframe.contentWindow?.removeEventListener("storage", handleStorageChange);
  };
}

/**
 * 9. PERFORMANCE OBSERVER
 * Monitor performance metrics and network requests
 */
export function observePerformance(
  iframeRef: React.RefObject<HTMLIFrameElement>
): CommunicationResult {
  const startTime = performance.now();

  try {
    const iframe = iframeRef.current;
    const perfData = iframe?.contentWindow?.performance.getEntriesByType(
      "resource"
    ) as PerformanceResourceTiming[];

    if (!perfData) {
      return {
        method: "performanceObserver",
        success: false,
        error: "Performance API not available",
        timestamp: new Date().toISOString(),
        duration: performance.now() - startTime,
      };
    }

    // Filter API requests
    const apiRequests = perfData.filter((entry) =>
      entry.name.includes("/api/")
    );

    return {
      method: "performanceObserver",
      success: true,
      data: {
        total: perfData.length,
        apiRequests: apiRequests.length,
        requests: apiRequests.map((r) => ({
          url: r.name,
          duration: r.duration,
          size: r.transferSize,
        })),
      },
      timestamp: new Date().toISOString(),
      duration: performance.now() - startTime,
    };
  } catch (err) {
    return {
      method: "performanceObserver",
      success: false,
      error: String(err),
      timestamp: new Date().toISOString(),
      duration: performance.now() - startTime,
    };
  }
}

/**
 * 10. MULTI-METHOD FALLBACK EXTRACTION
 * Try all methods in order until one succeeds
 */
export async function extractMultiplierMultiMethod(
  iframeRef: React.RefObject<HTMLIFrameElement>
): Promise<{
  value: number | null;
  method: string;
  results: CommunicationResult[];
}> {
  const results: CommunicationResult[] = [];

  // Method 1: PostMessage
  const pmResult = await sendPostMessage(iframeRef, { type: "GET_MULTIPLIER" });
  results.push(pmResult);
  if (pmResult.success && pmResult.data?.multiplier) {
    return {
      value: parseFloat(pmResult.data.multiplier),
      method: "postMessage",
      results,
    };
  }

  // Method 2: Window object access
  const woResult = await accessWindowObject(iframeRef, "Game.state.multiplier");
  results.push(woResult);
  if (woResult.success && woResult.data) {
    return {
      value: parseFloat(woResult.data),
      method: "windowObject",
      results,
    };
  }

  // Method 3: Call function
  const cfResult = await callIframeFunction(iframeRef, "Game.getMultiplier");
  results.push(cfResult);
  if (cfResult.success && cfResult.data) {
    return {
      value: parseFloat(cfResult.data),
      method: "callFunction",
      results,
    };
  }

  // Method 4: Regex search
  const rsResult = searchIframeText(iframeRef, /(\d+\.\d+)\s*[x×]/);
  results.push(rsResult);
  if (rsResult.success && rsResult.data?.length > 0) {
    const match = (rsResult.data[0] as string).match(/(\d+\.\d+)/);
    if (match) {
      return {
        value: parseFloat(match[1]),
        method: "regexSearch",
        results,
      };
    }
  }

  // All methods failed
  return {
    value: null,
    method: "failed",
    results,
  };
}

/**
 * TEST ALL METHODS AT ONCE
 * Useful for debugging which methods work with your iframe
 */
export async function testAllMethods(
  iframeRef: React.RefObject<HTMLIFrameElement>
): Promise<Record<string, CommunicationResult>> {
  const results: Record<string, CommunicationResult> = {};

  // Test 1: PostMessage
  results["postMessage"] = await sendPostMessage(iframeRef, {
    type: "PING",
  });

  // Test 2: Window object
  results["windowObject"] = await accessWindowObject(iframeRef, "window");

  // Test 3: Call function
  results["callFunction"] = await callIframeFunction(iframeRef, "console.log", [
    "test",
  ]);

  // Test 4: Regex search
  results["regexSearch"] = searchIframeText(iframeRef, /multiplier/i);

  // Test 5: Performance
  results["performance"] = observePerformance(iframeRef);

  return results;
}
