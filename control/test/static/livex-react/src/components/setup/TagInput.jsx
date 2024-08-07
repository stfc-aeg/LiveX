import React from 'react';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import { useState, useCallback, useRef } from 'react';
import { MultiSelect } from 'react-multi-select-component';
import { WithEndpoint } from 'odin-react';

const EndPointButton = WithEndpoint(Button);

function TagInput(props) {
    const {options} = props;
    const {metadataEndPoint} = props;
    const {field} = props;
    const {labelWidth} = props;

    const timer = useRef(null);

    const selectOptions = options.map(value => ({
      label: value,
      value: value,
      disabled: false
    }));

    const [selected, setSelected] = useState([]);


    // This onchange function essentially duplicates the functionality of the WithEndpoint
    // sendRequest function. That cannot be used for the MultiSelect normally, as the 'value' it
    // requires is an object (selectOptions above), but should send an array of the `value`s within.
    const sendTags = (selectedOptions) => {
      let fullpath = "fields/"+field+"/value"
      let value = selectedOptions.map(option => option.value);
      let result = metadataEndPoint.put(value, fullpath)
        .then((response) => {
          metadataEndPoint.mergeData(response, fullpath);
        })
        .catch((err) => {});
    }

    const onChangeHandler = useCallback((selectedOptions) => {
      setSelected(selectedOptions);
      if(timer.current){
          clearTimeout(timer.current);
      }
      // send data after a delay of a second
      timer.current = setTimeout(() => {console.log("Timer Elapsed. Sending Data"); sendTags(selectedOptions)}, 1000);
  }, []);

    return (
      <InputGroup>
        <InputGroup.Text style={{width:labelWidth}}>
          Experiment Tags
        </InputGroup.Text>
        <MultiSelect
          options={selectOptions}
          value={selected}
          onChange={onChangeHandler}
          labelledBy="Select tags"
          hasSelectAll={false}
        />
      </InputGroup>
    )
}

export default TagInput

