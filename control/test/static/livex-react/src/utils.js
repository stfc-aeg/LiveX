// Utility function that checks if a value is null or undefined. Returns 'null' if yes, value if no
export const checkNull = (val) => val === null || val === undefined ? 'null' : val.toFixed(4);