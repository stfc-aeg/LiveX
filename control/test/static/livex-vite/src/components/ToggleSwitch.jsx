import InputGroup from 'react-bootstrap/InputGroup';

import React, {useEffect, useState} from 'react';

import Switch from "react-switch";


const ToggleSwitch = (props) => {

    const {checked, value, id, label, onClick, disabled} = props;
    const [ischecked, setIsChecked] = useState(checked);

	useEffect(() => {
		setIsChecked(!!checked);
	}, [checked])

	const toggle = (check, event) => {
		setIsChecked(check);
		// console.log(check)
		// console.log(event)
		event.target.value = check;
		onClick(event)
	}
    return (
        <InputGroup.Text>
            <label id={id} style={{marginRight: "4px"}}>
				{label}:
			</label>
            <Switch
			checked={ischecked} onChange={toggle} disabled={disabled}
			onColor="#86d3ff" onHandleColor="#2693e6" handleDiameter={25}
			boxShadow="0px 1px 5px rgba(0, 0, 0, 0.6)" activeBoxShadow="0px 0px 1px 10px rgba(0, 0, 0, 0.2)"
            height={20} width={48}
			aria-labelledby={id} />
        </InputGroup.Text>
    )
}

export default ToggleSwitch;