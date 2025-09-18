import React, { useState, useCallback, useRef, useMemo } from 'react';
import InputGroup from 'react-bootstrap/InputGroup';
import Select from 'react-select';

function TagInput(props) {
  const { options, metadataEndPoint, field, labelWidth, currentValue } = props;
  const timer = useRef(null);

  // Memo for stable references prevents flickering
  const selectOptions = useMemo(
    () => options.map(value => ({label: value, value })),
    [options]
  );

  // Track selected values and not objects to avoid re-render due to comparison issues
  const [selectedValues, setSelectedValues] = useState(() =>
    Array.isArray(currentValue) ? currentValue : []
  );

  // Convert the values to objects for the select
  const selectedOptions = useMemo(
    () => selectOptions.filter(option => selectedValues.includes(option.value)),
    [selectOptions, selectedValues]
  );

  const sendTags = (values) => {
    let fullpath = `fields/${field}/value`;
    metadataEndPoint.put(values, fullpath)
      .then((response) => {
        metadataEndPoint.mergeData(response, fullpath);
      })
      .catch((err) => {});
  }

  const onChangeHandler = useCallback((newSelected) => {
    const values = newSelected ? newSelected.map(option => option.value) : [];
    setSelectedValues(values);

    if (timer.current) {
      clearTimeout(timer.current);
    }
    timer.current = setTimeout(() => {
      console.log("Timer Elapsed. Sending tag data.");
      sendTags(values);
    }, 1000);
  }, []);

  return (
    <InputGroup>
      <InputGroup.Text style={{ width: labelWidth }}>
        Experimental Tags:
      </InputGroup.Text>
      <div style={{ flex: 1 }}>
        <Select
          isMulti
          options={selectOptions}
          value={selectedOptions}
          onChange={onChangeHandler}
          styles={{
            menu: (provided) => ({ ...provided, zIndex: 1050 })
          }}  // Ensure dropdown appears above other elements (acq_id buttons, mostly)
        />
      </div>
    </InputGroup>
  );
}

export default TagInput;
