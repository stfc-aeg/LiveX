import React, { useState, useCallback, useRef } from 'react';
import InputGroup from 'react-bootstrap/InputGroup';
import Select from 'react-select';

function TagInput(props) {
  const { options, metadataEndPoint, field, labelWidth, currentValue } = props;
  const timer = useRef(null);

  const selectOptions = options.map(value => ({
    label: value,
    value: value
  }));

  const [selected, setSelected] = useState(() => {
    return Array.isArray(currentValue)
      ? currentValue.map(value => ({
          label: value,
          value: value
        }))
      : [];
  });

  const sendTags = (selectedOptions) => {
    let fullpath = "fields/" + field + "/value";
    let value = selectedOptions.map(option => option.value);
    metadataEndPoint.put(value, fullpath)
      .then((response) => {
        metadataEndPoint.mergeData(response, fullpath);
      })
      .catch((err) => {});
  }

  const onChangeHandler = useCallback((selectedOptions) => {
    setSelected(selectedOptions);
    if (timer.current) {
      clearTimeout(timer.current);
    }
    timer.current = setTimeout(() => {
      console.log("Timer Elapsed. Sending Data");
      sendTags(selectedOptions || []);
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
          value={selected}
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
