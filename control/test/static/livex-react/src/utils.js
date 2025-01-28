import * as React from 'react';

// Utility function that checks if a value is null or undefined. Returns 'null' if yes, value if no
export const checkNull = (val) => val === null || val === undefined ? 'null' : val.toFixed(4);

export const checkNullNoDp = (val) => val === null || val === undefined ? 'null' : val;

// usePrevious - to track the previous state of a variable
// https://phuoc.ng/collection/react-ref/save-the-previous-value-of-a-variable/
export const usePrevious = (value) => {
    const ref = React.useRef();
    React.useEffect(() => {
        ref.current = value;
    });
    return ref.current;
};
