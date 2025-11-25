/**
 * Iframe DOM Scanner
 * Continuously captures and analyzes iframe DOM structure
 * Identifies multiplier elements and their selectors
 */

export interface DOMElement {
  tag: string;
  id?: string;
  className?: string;
  text: string;
  html?: string;
  xpath: string;
  cssSelector?: string;
  attributes: Record<string, string>;
}

export interface ScanResult {
  timestamp: string;
  elements: DOMElement[];
  multiplierElements: DOMElement[];
  numericPatterns: Array<{
    element: DOMElement;
    value: number;
    format: string;
  }>;
}

/**
 * Generate XPath for an element
 */
function getXPath(element: Element): string {
  if (element.id !== "")
    return `//*[@id="${element.id}"]`;

  if (element === element.ownerDocument.body)
    return "//*";

  const ix: number[] = [];
  let parent = element.parentNode;

  while (parent && parent.nodeType !== Node.DOCUMENT_NODE) {
    const siblings = parent.childNodes;
    let count = 0;

    for (let i = 0; i < siblings.length; i++) {
      const sibling = siblings[i];

      if (sibling === element) {
        ix.unshift(count + 1);
        break;
      }

      if (sibling.nodeType === Node.ELEMENT_NODE &&
          (sibling as Element).nodeName === element.nodeName) {
        count++;
      }
    }

    element = parent as Element;
    parent = parent.parentNode;
  }

  return ix.length ? `/${ix.map(i => `*[${i}]`).join("/")}` : "/";
}

/**
 * Generate CSS selector for an element
 */
function getCSSSelector(element: Element): string {
  if (element.id)
    return `#${element.id}`;

  const path: string[] = [];
  let current: Element | null = element;

  while (current && current.nodeType === Node.ELEMENT_NODE) {
    let selector = current.nodeName.toLowerCase();

    if (current.id) {
      selector += `#${current.id}`;
      path.unshift(selector);
      break;
    } else {
      if (current.className) {
        const classes = current.className.split(" ").filter(c => c);
        if (classes.length) {
          selector += `.${classes.join(".")}`;
        }
      }

      const sibling = current.previousElementSibling;
      let index = 1;

      if (sibling) {
        for (let i = current.parentNode?.children.length || 0; i >= 0; i--) {
          if (current.parentNode?.children[i] === current) {
            index = i + 1;
            break;
          }
        }
        selector += `:nth-child(${index})`;
      }
    }

    path.unshift(selector);
    current = current.parentElement;
  }

  return path.join(" > ");
}

/**
 * Extract all relevant DOM elements from iframe
 */
function extractElements(iframeDoc: Document): DOMElement[] {
  const elements: DOMElement[] = [];
  const walker = iframeDoc.createTreeWalker(
    iframeDoc.body,
    NodeFilter.SHOW_ELEMENT,
    null
  );

  let node: Element | null;
  while (node = walker.nextNode() as Element | null) {
    // Skip script and style tags
    if (node.tagName === "SCRIPT" || node.tagName === "STYLE") continue;

    const text = node.innerText?.trim() || node.textContent?.trim() || "";

    // Only include elements with text content (reduce noise)
    if (!text && node.children.length === 0) continue;

    elements.push({
      tag: node.tagName.toLowerCase(),
      id: node.id || undefined,
      className: node.className || undefined,
      text: text.substring(0, 200), // Limit text length
      html: node.outerHTML.substring(0, 500),
      xpath: getXPath(node),
      cssSelector: getCSSSelector(node),
      attributes: Array.from(node.attributes).reduce((acc, attr) => {
        acc[attr.name] = attr.value;
        return acc;
      }, {} as Record<string, string>),
    });
  }

  return elements;
}

/**
 * Identify multiplier-related elements
 */
function identifyMultiplierElements(elements: DOMElement[]): DOMElement[] {
  const multiplierKeywords = [
    "multiplier",
    "crash",
    "coefficient",
    "x.xx",
    "1.",
    "2.",
    "3.",
    "4.",
    "5.",
  ];

  return elements.filter(el => {
    const textLower = el.text.toLowerCase();
    const classLower = (el.className || "").toLowerCase();

    return (
      multiplierKeywords.some(kw => textLower.includes(kw)) ||
      multiplierKeywords.some(kw => classLower.includes(kw)) ||
      /\d+\.\d+/.test(el.text) // Matches decimal numbers like 1.23
    );
  });
}

/**
 * Extract numeric patterns from elements
 */
function extractNumericPatterns(
  elements: DOMElement[]
): Array<{ element: DOMElement; value: number; format: string }> {
  const patterns: Array<{ element: DOMElement; value: number; format: string }> = [];

  elements.forEach(el => {
    // Pattern 1: X.XX format
    const decimalMatch = el.text.match(/(\d+\.\d+)/g);
    if (decimalMatch) {
      decimalMatch.forEach(match => {
        const value = parseFloat(match);
        if (value > 0 && value < 10000) {
          patterns.push({
            element: el,
            value,
            format: `${match} (decimal)`,
          });
        }
      });
    }

    // Pattern 2: XXx or XX× format
    const multiplierMatch = el.text.match(/(\d+(?:\.\d+)?)\s*[x×]/gi);
    if (multiplierMatch) {
      multiplierMatch.forEach(match => {
        const value = parseFloat(match.replace(/[x×]/gi, ""));
        if (value > 0 && value < 10000) {
          patterns.push({
            element: el,
            value,
            format: `${match} (with x/×)`,
          });
        }
      });
    }

    // Pattern 3: Just numbers (1, 2, 3+ digits)
    const numberMatch = el.text.match(/^(\d+(?:\.\d{1,2})?)$/);
    if (numberMatch) {
      const value = parseFloat(numberMatch[1]);
      if (value > 1 && value < 10000) {
        patterns.push({
          element: el,
          value,
          format: `${numberMatch[1]} (plain number)`,
        });
      }
    }
  });

  // Remove duplicates and sort by value
  const unique = patterns.reduce((acc, current) => {
    const exists = acc.some(
      p => p.element.xpath === current.element.xpath && p.value === current.value
    );
    if (!exists) acc.push(current);
    return acc;
  }, [] as typeof patterns);

  return unique.sort((a, b) => b.value - a.value);
}

/**
 * Continuous DOM scanner - runs for specified duration
 */
export async function startContinuousDOMScan(
  iframeRef: React.RefObject<HTMLIFrameElement>,
  durationSeconds: number = 10,
  onUpdate?: (result: ScanResult) => void
): Promise<ScanResult[]> {
  const results: ScanResult[] = [];
  const startTime = Date.now();
  const endTime = startTime + durationSeconds * 1000;

  return new Promise((resolve) => {
    const scanInterval = setInterval(() => {
      const iframe = iframeRef.current;
      if (!iframe || !iframe.contentDocument) {
        clearInterval(scanInterval);
        resolve(results);
        return;
      }

      const allElements = extractElements(iframe.contentDocument);
      const multiplierElements = identifyMultiplierElements(allElements);
      const numericPatterns = extractNumericPatterns(multiplierElements);

      const result: ScanResult = {
        timestamp: new Date().toISOString(),
        elements: allElements,
        multiplierElements,
        numericPatterns,
      };

      results.push(result);
      onUpdate?.(result);

      // Stop after duration
      if (Date.now() >= endTime) {
        clearInterval(scanInterval);
        resolve(results);
      }
    }, 500); // Scan every 500ms
  });
}

/**
 * Generate analysis report from scan results
 */
export function generateScanReport(results: ScanResult[]): string {
  let report = "=== IFRAME DOM SCAN REPORT ===\n\n";

  report += `Total Scans: ${results.length}\n`;
  report += `Duration: ${results.length * 0.5} seconds\n`;
  report += `Timespan: ${results[0]?.timestamp} to ${results[results.length - 1]?.timestamp}\n\n`;

  // Unique multiplier elements found
  const uniqueMultiplierElements = new Map<string, DOMElement>();
  const uniquePatterns = new Map<number, Array<{ xpath: string; format: string }>>();

  results.forEach(result => {
    result.multiplierElements.forEach(el => {
      uniqueMultiplierElements.set(el.xpath, el);
    });

    result.numericPatterns.forEach(pattern => {
      if (!uniquePatterns.has(pattern.value)) {
        uniquePatterns.set(pattern.value, []);
      }
      uniquePatterns.get(pattern.value)!.push({
        xpath: pattern.element.xpath,
        format: pattern.format,
      });
    });
  });

  report += `=== IDENTIFIED MULTIPLIER ELEMENTS (${uniqueMultiplierElements.size}) ===\n`;
  Array.from(uniqueMultiplierElements.values()).forEach(el => {
    report += `\nTag: <${el.tag}>\n`;
    report += `ID: ${el.id || "N/A"}\n`;
    report += `Class: ${el.className || "N/A"}\n`;
    report += `Text: "${el.text}"\n`;
    report += `XPath: ${el.xpath}\n`;
    report += `CSS Selector: ${el.cssSelector}\n`;
    report += `Attributes: ${JSON.stringify(el.attributes)}\n`;
  });

  report += `\n=== NUMERIC PATTERNS FOUND (${uniquePatterns.size}) ===\n`;
  Array.from(uniquePatterns.entries())
    .sort((a, b) => b[0] - a[0])
    .forEach(([value, locations]) => {
      report += `\nMultiplier: ${value.toFixed(2)}x\n`;
      report += `  Found in ${locations.length} location(s):\n`;
      locations.forEach(loc => {
        report += `    - ${loc.xpath} (${loc.format})\n`;
      });
    });

  report += `\n=== SCAN TIMELINE ===\n`;
  results.forEach((result, idx) => {
    report += `\n[${idx}] ${result.timestamp}\n`;
    report += `  Elements: ${result.elements.length}\n`;
    report += `  Multiplier Elements: ${result.multiplierElements.length}\n`;
    report += `  Numeric Patterns: ${result.numericPatterns.length}\n`;
    if (result.numericPatterns.length > 0) {
      report += `  Values: ${result.numericPatterns.map(p => p.value.toFixed(2)).join(", ")}x\n`;
    }
  });

  return report;
}

/**
 * Export scan results to JSON
 */
export function exportScanResults(results: ScanResult[]): string {
  return JSON.stringify(results, null, 2);
}

/**
 * Get the most common/stable multiplier value from scan results
 */
export function getMostReliableMultiplier(
  results: ScanResult[]
): { value: number; confidence: number; frequency: number } | null {
  const valueFrequency = new Map<number, number>();

  results.forEach(result => {
    result.numericPatterns.forEach(pattern => {
      const rounded = Math.round(pattern.value * 100) / 100; // Round to 2 decimals
      valueFrequency.set(rounded, (valueFrequency.get(rounded) || 0) + 1);
    });
  });

  if (valueFrequency.size === 0) return null;

  const entries = Array.from(valueFrequency.entries()).sort((a, b) => b[1] - a[1]);
  const [value, frequency] = entries[0];

  return {
    value,
    confidence: frequency / (results.length * 3), // Rough confidence estimate
    frequency,
  };
}
