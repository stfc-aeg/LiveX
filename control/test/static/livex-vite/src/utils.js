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

export const floatingLabelStyle = {
    width: "60%",
    border: '1px solid lightblue',
    backgroundColor: '#e0f7ff',
    borderRadius: '0.375rem'
}

export const floatingInputStyle = {
  border: "1px solid #ced4da", // thin Bootstrap-like grey border
  borderRadius: "0.375rem",    // Bootstrap default rounded corners
};