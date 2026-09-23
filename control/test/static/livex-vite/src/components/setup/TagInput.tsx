import type { AdapterEndpoint } from '@dssg/odin-react';
import type { MetadataEndpointTypes } from '../../EndpointTypes';

import { useState, useCallback, useMemo } from 'react';
import InputGroup from 'react-bootstrap/InputGroup';
import Select from 'react-select';

interface TagInputProps {
  options: string[];
  metadataEndPoint: AdapterEndpoint<MetadataEndpointTypes>;
  field: string;
  labelWidth: number | string;
  currentValue: string | string[];
}

function TagInput(props: TagInputProps) {
  const { options, metadataEndPoint, field, labelWidth, currentValue } = props;

  const parseTags = (value: string | string[]): string[] => {
    if (Array.isArray(value)) {
      return value;
    }

    try {
      const parsedValue = JSON.parse(value);
      return Array.isArray(parsedValue) ? parsedValue : [];
    } catch {
      return [];
    }
  };

  // Memo for stable references prevents flickering
  const selectOptions = useMemo(
    () => options.map(value => ({label: value, value })),
    [options]
  );

  // Track selected values and not objects to avoid re-render due to comparison issues
  const [selectedValues, setSelectedValues] = useState(() => parseTags(currentValue));

  // Convert the values to objects for the select
  const selectedOptions = useMemo(
    () => selectOptions.filter(option => selectedValues.includes(option.value)),
    [selectOptions, selectedValues]
  );

  const sendTags = (values: string[]) => {
    const fullpath = `fields/${field}/value`;
    const valueParam = { 'value': JSON.stringify(values) };
    metadataEndPoint.put(valueParam, fullpath)
      .catch((err) => { console.log(err) });
  }

  const onChangeHandler = useCallback(
    (newValue: readonly {label: string; value: string}[] | null) => {
      const values = newValue ? newValue.map(option => option.value) : [];
      setSelectedValues(values);
      sendTags(values);
    },
    [metadataEndPoint, field]
  );

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
